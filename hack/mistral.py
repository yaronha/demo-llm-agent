import torch
from langchain import PromptTemplate
from langchain import HuggingFacePipeline
from langchain.chains import LLMChain

from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, pipeline

import warnings
warnings.filterwarnings('ignore')

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"  # v0.2

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME, torch_dtype=torch.float32,
    trust_remote_code=True,
)

generation_config = GenerationConfig.from_pretrained(MODEL_NAME)
generation_config.max_new_tokens = 1024
generation_config.temperature = 0.0001
generation_config.top_p = 0.95
generation_config.do_sample = True
generation_config.repetition_penalty = 1.15

pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    return_full_text=True,
    generation_config=generation_config,
)

llm = HuggingFacePipeline(
    pipeline=pipeline,
    )

template = """Question: {question}

Answer: """
prompt = PromptTemplate(
    template=template,
    input_variables=['question']
)

# user question
question = "Which NFL team won the Super Bowl in the 2010 season?"

# Create llm chain
llm_chain = LLMChain(llm=llm, prompt=prompt)
print(llm_chain.run(question))
