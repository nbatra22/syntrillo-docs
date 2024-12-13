from syntrillo.chatbots.after_hours.db_operations import get_similar_docs, initialize_db
from syntrillo.chatbots.after_hours.models import Messages, db
import json
import boto3
import time
import uuid

from syntrillo.system.logger import logger

def create_message(user_id, content, sender_role, session_id):
    new_message = Messages(user_id=user_id.bytes, content=content, sender_role=sender_role, session_id=session_id)
    db.session.add(new_message)
    db.session.commit()


def initialize_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name='us-east-1'
    )


def model_invoke(prompt, model, user_id, session_id, is_history=False):
    logger.info(f"Invoking model {model}")
    messages = Messages.query.filter_by(user_id=user_id, session_id=session_id).order_by(Messages.timestamp.asc()).all()
    bedrock = initialize_bedrock_client()
    model_mapping = {
        "claude-3": "anthropic.claude-3-sonnet-20240229-v1:0",
        "claude-3-5": "anthropic.claude-3-5-sonnet-20240620-v1:0"
    }
    model_sequence = [model, "claude-3-5"] if model == "claude-3" else ["claude-3-5", "claude-3"]
    messages_history = [msg.to_dict() for msg in messages]
    messages_history.append(
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}],
        }
    )
    body = json.dumps({
        "messages": messages_history,
        "max_tokens": 2000,
        "top_p": 0.2,
        "temperature": 0,
        "anthropic_version": "bedrock-2023-05-31"
    })

    # Try invoking the primary model, then fallback if it fails
    for attempt, model_name in enumerate(model_sequence, start=1):
        model_id = model_mapping[model_name]
        try:
            response = bedrock.invoke_model(
                body=body,
                modelId=model_id,
                accept="application/json",
                contentType="application/json"
            )
            json_response = json.loads(response.get('body').read())['content'][0]['text']
            if is_history:
                create_message(user_id=user_id, content=prompt, sender_role='user', session_id=session_id)
                create_message(user_id=user_id, content=json_response, sender_role='assistant', session_id=session_id)
            return json_response
        except Exception as e:
            print(f"Error invoking model {model_name}: {str(e)}")
            if attempt == len(model_sequence):
                # Retry mechanism exhausted
                time.sleep(2)  # Optional: add delay before retrying
                # Retry the original sequence once more
                for retry_model_name in model_sequence:
                    model_id = model_mapping[retry_model_name]
                    try:
                        response = bedrock.invoke_model(
                            body=body,
                            modelId=model_id,
                            accept="application/json",
                            contentType="application/json"
                        )
                        json_response = json.loads(response.get('body').read())['content'][0]['text']
                        if is_history:
                            create_message(user_id=user_id, content=prompt, sender_role='user', session_id=session_id)
                            create_message(user_id=user_id, content=json_response, sender_role='assistant', session_id=session_id)
                        return json_response
                    except Exception as retry_exception:
                        print(f"Retry failed with model {retry_model_name}: {str(retry_exception)}")
                raise Exception("Both Claude-3 and Claude-3.5 models failed after retries.")


def process_device_manual_query(query, collection_name, model, user_id, session_id):
    db = initialize_db(collection_name)
    
    similar_docs = get_similar_docs(db, query)
    context = "\n\n".join([doc[0].page_content for doc in similar_docs])
    
    prompt_template = f"""You are a helpful assistant that answers questions about device manuals using the information provided in the context below.

    Context:
    {context}

    Question:
    {query}

    Please provide a concise and accurate answer based on the given context. If the information is not available in the context, please state that you don't have the relevant information."""

    return model_invoke(prompt_template, model, user_id, session_id, is_history=True)


def ask_follow_up_questions(initial_query, model, user_id, session_id):
    prompt = f"""Based on the following patient information and any previous questions and answers, generate a relevant follow-up question to gather more information about the patient's condition, symptoms, or medical history. The questions should be dynamic and based on the context of the conversation.
    Initial patient information: {initial_query}
    If you have gathered sufficient information. Otherwise, provide the next follow-up question.
    If symptoms appear severe or urgent, advise the user to consult a healthcare professional promptly.
    Response:"""
    response = model_invoke(prompt, model, user_id, session_id, is_history=True)
    return response


def ask_generic_questions(initial_query, model, user_id, session_id):
    prompt = f"""You are Syntrillio, a helpful medical assistant chatbot. Based on the user's question, "{initial_query}", provide a clear and informative response related to medical topics. If symptoms appear severe or urgent, advise the user to consult a healthcare professional promptly.
    Response:"""
    response = model_invoke(prompt, model, user_id, session_id, is_history=True)
    return response


def classify_query(query, model, user_id, session_id):
    prompt_template = f"""
    Classify the following query into one of two categories:
    1. Device manual related query
    2. Medical guideline or symptom related query

    Query: {query}

    Respond with a JSON object containing only the class number, like this:
    {{"class": 1}} or {{"class": 2}}

    Classification:
    """
    response = model_invoke(prompt_template, model, user_id, session_id)
    return json.loads(response)


def process_query(query, model, user_id, session_id):
    # create_message(user_id=user_id, content=query, sender_role='user', session_id=session_id)
    class_num = classify_query(query, model, user_id, session_id)
    if class_num['class'] == 1:
        # Device manual related query
        collection_name = "device_manuals"  # Replace with your actual collection name for device manuals
        return process_device_manual_query(query, collection_name, model, user_id, session_id)
    elif class_num['class'] == 2:
        # Patient information related query
        follow_up_data = ask_follow_up_questions(query, model, user_id, session_id)
        return follow_up_data
    else:
        # Patient information related query
        follow_up_data = ask_generic_questions(query, model, user_id, session_id)
        return follow_up_data