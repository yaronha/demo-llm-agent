import os.path

from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import WebBaseLoader

from app.config import config, get_vector_db
from app.data.doc_loader import DataLoader, get_data_loader, get_loader_obj


def test_data_loader():
    loader = WebBaseLoader(
        [
            "https://milvus.io/docs/overview.md",
        ]
    )

    data_loader = DataLoader(config)
    data_loader.load(loader, metadata={"xx": "web"})
    print(os.path.realpath(config.vector_store_path))


def test_load():
    data_loader = get_data_loader(config)
    loader_obj = get_loader_obj("https://milvus.io/docs/overview.md", loader_type="web")
    data_loader.load(loader_obj)


def test_vector_db():
    vector_store = get_vector_db(config)
    results = vector_store.similarity_search(
        "Can you please provide me with information about the mobile plans?"
    )
    print("results:", results)


def test_retrieval():
    vector_store = get_vector_db(config)
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    question = "What is a vector?"
    filter = {"chunk": 1}
    # filter = {"chunk": {"$eq": "3"}}
    # filter = {}
    search_args = {"filter": dict(filter)} if filter else {}
    dr = document_retrevial(llm, vector_store, verbose=True, **search_args)
    answer = dr.get_text_answer(question)
    print(answer)


def test_search():
    vector_store = get_vector_db(config)
    filter = {"chunk": 1}
    results = vector_store.similarity_search("What is milvus?", filter=filter)  # {}{})
    print()
    print(results)


def test_llm():
    import sys

    from langchain.llms import LlamaCpp

    # enable verbose to debug the LLM's operation
    verbose = False

    llm = LlamaCpp(
        model_path="/home/chris/MODELS/synthia-7b-v2.0-16k.Q4_K_M.gguf",
        # max tokens the model can account for when processing a response
        # make it large enough for the question and answer
        n_ctx=4096,
        # number of layers to offload to the GPU
        # GPU is not strictly required but it does help
        n_gpu_layers=32,
        # number of tokens in the prompt that are fed into the model at a time
        n_batch=1024,
        # use half precision for key/value cache; set to True per langchain doc
        f16_kv=True,
        verbose=verbose,
    )

    while True:
        question = input("Ask me a question: ")
        if question == "stop":
            sys.exit(1)
        output = llm(
            question,
            max_tokens=4096,
            temperature=0.2,
            # nucleus sampling (mass probability index)
            # controls the cumulative probability of the generated tokens
            # the higher top_p the more diversity in the output
            top_p=0.1,
        )
        print(f"\n{output}")
