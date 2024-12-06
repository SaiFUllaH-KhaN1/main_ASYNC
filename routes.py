from flask import Flask, render_template, request, Response, jsonify, session, send_from_directory, flash, redirect, url_for
import os
from dotenv import load_dotenv
import json
import prompt_logics as LCD
from flask_caching import Cache
import shutil 
from werkzeug.datastructures import FileStorage
from flask_basicauth import BasicAuth
import time
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS
from functools import wraps
import io
import openai
import traceback
import prompt_logics as LCD
import logging
import sys, socket
# from gevent.pywsgi import WSGIServer # in local development use, for gevent in local served  
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logger = logging
logger.basicConfig(level= logging.DEBUG, format= log_format)

load_dotenv(dotenv_path="HUGGINGFACEHUB_API_TOKEN.env")

openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')


# Configuration for the cache directory
cache_dir = 'cache'

# Check if the cache directory exists, and create it if it does not
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    logger.info(f"Cache directory '{cache_dir}' was created.")
else:
    logger.info(f"Cache directory '{cache_dir}' already exists.")


app.config['BASIC_AUTH_REALM'] = 'realm'
app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD')
basic_auth = BasicAuth(app)

app.config['CACHE_TYPE'] = 'FileSystemCache' 
app.config['CACHE_DIR'] = cache_dir # path to server cache folder
app.config['CACHE_THRESHOLD'] = 1000
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

cache = Cache(app)

allowed_origins = [
    "https://thinglink.local",
    "https://thinglink.local:3000",
    "https://sandbox.thinglink.com",
    "https://thinglink.com",
    "https://www.thinglink.com"
]

# Configure CORS for multiple routes with specific settings
cors = CORS(app, supports_credentials=True, resources={
    r"/process_data": {"origins": allowed_origins},
    r"/process_data_without_file": {"origins": allowed_origins},
    r"/decide": {"origins": allowed_origins},
    r"/decide_without_file": {"origins": allowed_origins},
    r"/generate_course": {"origins": allowed_origins},
    r"/generate_course_without_file": {"origins": allowed_origins},
    r"/find_images": {"origins": allowed_origins}
})

### TOKEN DECORATORS ###




### MANUAL DELETION OF all folders starting with faiss_index_ ###
def delete_indexes():
    """
    Deletes directories starting with 'faiss_index_' in the root directory of the app.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    for item in os.listdir(base_path):
        dir_path = os.path.join(base_path, item)
        if os.path.isdir(dir_path) and item.startswith("faiss_index_"):
            logger.info(f"Deleting Faiss directory: {dir_path}")
            shutil.rmtree(dir_path)
        elif os.path.isdir(dir_path) and item.startswith("imagefolder_"):
            logger.info(f"Deleting image directory: {dir_path}")
            shutil.rmtree(dir_path)
        elif os.path.isdir(dir_path) and item.startswith("audio_"):
            logger.info(f"Deleting audio directory: {dir_path}")
            shutil.rmtree(dir_path)
        elif os.path.isdir(dir_path) and item.startswith("pdf_dir"):
            logger.info(f"Deleting pdf directory: {dir_path}")
            shutil.rmtree(dir_path)

@app.route("/cron", methods=['POST'])
@basic_auth.required
def cron():
    delete_indexes()
    logger.info("Deleted FAISS index")
    return jsonify(message="FAISS and imagefolder and audio index directories deleted")
###     ###     ### 

### SCHEDULED DELETION OF folders of imagefolder_ and faiss_index_ ###
def delete_old_directories():
    time_to_delete_files_older_than = timedelta(seconds=30)
    logger.info(f"Scheduler is running the delete_old_directories function to delete files older than {time_to_delete_files_older_than}.")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    for item in os.listdir(base_path):
        dir_path = os.path.join(base_path, item)
        if os.path.isdir(dir_path) and item.startswith("faiss_index_") or item.startswith("imagefolder_") or item.startswith("audio_") or item.startswith("pdf_dir"):
            # Check if directory is older than a specified time
            dir_age = datetime.fromtimestamp(os.path.getmtime(dir_path))
            if datetime.now() - dir_age > time_to_delete_files_older_than:
                logger.info(f"Deleting directory: {dir_path}, it has modified date of {dir_age}")
                shutil.rmtree(dir_path)
###     ###     ###

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", 47200))
except socket.error:
    logger.info("!!!scheduler already started, DO NOTHING")
else:
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_old_directories, 'interval', seconds=30)
    scheduler.start()

# Configuration for the audio directory
audio_dir = 'audio_files'
# Check if the cache directory exists, and create it if it does not
if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)
    logger.info(f"Audio directory '{audio_dir}' was created.")
else:
    logger.info(f"Audio directory '{audio_dir}' already exists.")


@app.route("/decide", methods=["GET", "POST"])
def decide():

    if request.method == 'POST':
        scenario = request.form.get('scenario')
        logger.info(f"Scenario type:{scenario}")

        model_type = request.args.get('model', 'azure') # to set default model
        model_name = request.args.get('modelName', 'gpt') # to set default model name

        start_time = time.time() # Timer starts at the Post

        if scenario:

            try:
                if model_type == "gemini":
                    llm = ChatGoogleGenerativeAI(model=model_name,temperature=0)
                    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

                elif model_type == "azure":
                    llm = AzureChatOpenAI(deployment_name=model_name, temperature=0,
                                        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION")
                                        )
                    embeddings = AzureOpenAIEmbeddings(azure_deployment="text-embedding-ada-002")

                logger.info(f"LLM is :: {llm}\n embedding is :: {embeddings}\n")

                chain, query = LCD.PRODUCE_LEARNING_OBJ_COURSE(scenario, llm, model_type)

                logger.info("response_LO_CA started")
                response_LO_CA = chain({"scenario": query})
                logger.info(f"{response_LO_CA}")
                logger.info("response_LO_CA ended")

                end_time = time.time()
                execution_time = end_time - start_time
                minutes, seconds = divmod(execution_time, 60)
                formatted_time = f"{int(minutes):02}:{int(seconds):02}"
                execution_time_block = {"executionTime":f"{formatted_time}"}
                logger.info(f"{response_LO_CA['text']}")
                response_with_time = json.loads(response_LO_CA['text']) 
                response_with_time.update(execution_time_block)
                logger.info(f"{json.dumps(response_with_time)}")

                return Response(json.dumps(response_with_time), mimetype='application/json')
                # return jsonify(response_LO_CA['text'])       

            except Exception as e:
                logger.info(f"An error occurred or abrupt Model change: {str(e)}")
                logger.info(traceback.format_exc())
                return jsonify(error=f"An error occurred or abrupt Model change: {str(e)}")

        else:
            logger.info("None")
        
        logger.info("Unexpected Fault or Interruption")
        return jsonify(error="Unexpected Fault or Interruption")
    

# @app.teardown_appcontext
# def shutdown_scheduler(exception=None):
#     # This app route shutsdown scheduler when app context is destroyed
#     if scheduler.running:
#         scheduler.shutdown()
#     try:
#         sock.close()
#     except Exception as e:
#         print(f"Error closing the socket: {e}")

if __name__ == '__main__': # runs in local deployment only, and NOT in docker since CMD command takes care of it

    try:
        app.run(use_reloader=False)  # use_reloader=False to avoid duplicate jobs
        # for runing the app with eventlet WSGI server
        # http_server = WSGIServer(("127.0.0.1", 5000), app)
        # http_server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
