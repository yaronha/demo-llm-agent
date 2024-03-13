import mlrun
from mlrun import serving
from mlrun.utils import get_caller_globals

from src.config import config as default_config
from src.data.sessions import get_session_store

# pipelines cache
pipelines = {}


class AppPipeline:
    def __init__(self, name=None, graph=None, config=None):
        self.name = name or ""
        self._config = config or default_config
        self.verbose = self._config.verbose
        self.session_store = get_session_store(self._config)
        self._graph = None
        self._server = None

        if graph:
            self.graph = graph

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
            server = serving.create_graph_server(
                graph=self.graph,
                parameters={},
                verbose=self.verbose,
                graph_initializer=self.lc_initializer,
            )
            server.init_states(context=None, namespace=namespace)
            server.init_object(namespace)
            self._server = server
            return server
        return self._server

    def lc_initializer(self, server):
        context = server.context
        if getattr(context, "_config", None) is None:
            context._config = self._config
        if getattr(context, "session_store", None) is None:
            context.session_store = self.session_store

    def run(self, event, db_session=None):
        # todo: pass sql db_session to steps via context or event
        server = self.get_server()
        try:
            resp = server.test("", body=event)
        finally:
            server.wait_for_completion()

        print("resp: ", resp)
        return resp.results


def get_or_create_pipeline(name, graph, config=None):
    """Get or create a pipeline instance.

    Args:
        name (str): pipeline name
        graph (Union[list, dict]): pipeline graph.
        config (AppConfig, optional): app config. Defaults to None.
    """
    if name in pipelines:
        return pipelines[name]
    pipeline = AppPipeline(name, graph, config)
    pipelines[name] = pipeline
    return pipeline
