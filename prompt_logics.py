# from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
import shutil
from langchain_core.prompts import PromptTemplate

promptSelector = PromptTemplate(
    input_variables=["scenario"],
    template="""
    Tell me a sentence about this scenario of human input given in simple json format.

    'Human Input': ({scenario})
    """
)

def PRODUCE_LEARNING_OBJ_COURSE(query, llm, model_type):
    print("PRODUCE_LEARNING_OBJ_COURSE Initiated!")
    if model_type=="gemini":
        chain = LLMChain(prompt=promptSelector, llm=llm.bind(generation_config={"response_mime_type": "application/json"}))    
    else:
        chain = LLMChain(prompt=promptSelector, llm=llm.bind(response_format={"type": "json_object"}))
    return chain, query