import asyncio
import importlib
import inspect
from collections import OrderedDict

import storey
import mlrun
from mlrun import serving
from mlrun.utils import get_caller_globals

from src.data.sessions import get_session_store
from src.config import config as default_config, logger
from src.schema import PipelineEvent, TerminateResponse


class ChainRunner(storey.Flow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_async = asyncio.iscoroutinefunction(self._run)

    def _run(self, event: PipelineEvent):
        raise NotImplementedError()

    def __call__(self, event: PipelineEvent):
        return self._run(event)

    def post_init(self, mode="sync"):
        pass

    async def _do(self, event):
        if event is storey.dtypes._termination_obj:
            return await self._do_downstream(storey.dtypes._termination_obj)
        else:
            print("step name: ", self.name)
            element = self._get_event_or_body(event)
            if self._is_async:
                resp = await self._run(element)
            else:
                resp = self._run(element)
            if resp:
                for key, val in resp.items():
                    element.results[key] = val
                if "answer" in resp:
                    element.query = resp["answer"]
                mapped_event = self._user_fn_output_to_event(event, element)
                await self._do_downstream(mapped_event)


class SessionLoader(storey.Flow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _do(self, event):
        if event is storey.dtypes._termination_obj:
            return await self._do_downstream(storey.dtypes._termination_obj)
        else:
            element = self._get_event_or_body(event)
            if isinstance(element, dict):
                element = PipelineEvent(**element)

            self.context.session_store.read_state(
                element
            )
            mapped_event = self._user_fn_output_to_event(event, element)
            await self._do_downstream(mapped_event)


class HistorySaver(ChainRunner):

    def __init__(
        self, answer_key: str = None, question_key: str = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.answer_key = answer_key or "answer"
        self.question_key = question_key

    async def _run(self, event: PipelineEvent):
        question = (
            event.results[self.question_key]
            if self.question_key
            else event.original_query
        )
        event.conversation.add_message("Human", question)
        event.conversation.add_message("AI", event.results[self.answer_key])

        self.context.session_store.save(event)
        return event.results


class AppPipeline:
    def __init__(self, name=None, config=None):
        self.name = name or ""
        self._config = config or default_config
        self.verbose = self._config.verbose
        self.session_store = get_session_store(self._config)
        self._graph = None
        self._server = None

    @property
    def graph(self) -> serving.states.RootFlowStep:
        return self._graph

    @graph.setter
    def graph(self, graph):
        if isinstance(graph, list):
            if not graph:
                raise ValueError("graph list must not be empty")
            graph_obj = mlrun.serving.states.RootFlowStep()
            step = graph_obj
            for item in graph:
                if isinstance(item, dict):
                    step = step.to(**item)
                else:
                    step = step.to(item)
            step.respond()
            self._graph = graph_obj
            return

        if isinstance(graph, dict):
            graph = mlrun.serving.states.RootFlowStep.from_dict(graph)
        self._graph = graph

    def get_server(self):
        if self._server is None:
            namespace = get_caller_globals()
            server = serving.create_graph_server(graph=self.graph, parameters={}, verbose=self.verbose,
                                         graph_initializer=self.lc_initializer)
            server.init_states(context=None, namespace=namespace)
            server.init_object(namespace)
            return server
        return self._server

    def lc_initializer(self, server):
        context = server.context
        if getattr(context, "_config", None) is None:
            context._config = self._config
        if getattr(context, "session_store", None) is None:
            context.session_store = self.session_store

    def post_init(self):
        self.graph.to(SessionLoader()).to(name="s1", class_name="RefineQuery").to(name="s2", class_name="MultiRetriever").to(HistorySaver()).respond()
        print(self.graph.to_yaml())

    def run(self, event: PipelineEvent, db_session=None):
        server = self.get_server()
        try:
            resp = server.test("", body=event)
        finally:
            server.wait_for_completion()

        print("resp: ", resp)
        return resp.results
