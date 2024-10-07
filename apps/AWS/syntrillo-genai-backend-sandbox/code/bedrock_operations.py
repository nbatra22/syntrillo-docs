from db_operations import get_similar_docs, initialize_db
import json
import boto3



def initialize_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        #aws_access_key_id=aws_access_key_id,
        #aws_secret_access_key=aws_secret_access_key,
        region_name='us-east-1'
    )

def model_invoke(prompt, model):
    bedrock = initialize_bedrock_client()
    model_mapping = {
        "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
        "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0"
    }
    model_id = model_mapping[model]

    body = json.dumps({
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "max_tokens": 2000,
        "top_p": 0.2,
        "temperature": 0,
        "anthropic_version": "bedrock-2023-05-31"
    })

    try:
        response = bedrock.invoke_model(
            body=body,
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )
        return json.loads(response.get('body').read())['content'][0]['text']
    except Exception as e:
        raise Exception(f"Error invoking Bedrock model: {str(e)}")


def get_answer_symptoms(question, context, collection_name, model):
    prompt_template = f"""You are a helpful assistant that answers questions directly and only using the information provided in the context below.

    Guidance for answers:
        - Always use English as the language in your responses.
        - In your answers, always use a professional tone.
        - If the context does not contain the answer, say "there are no relevant Syntrillo expert recommendations for this patient."
        - IMPORTANT: Do not include any introductory or summarizing statements. Start immediately with numbered recommendations.
    Now read this context below and answer the question at the bottom.

    ***Context:
    {context}

    ***Question:
    {question}

    **INSTRUCTIONS**
    Answer the user QUESTION ONLY using the DOCUMENT Context as a reference. These documents are retrieved from '{collection_name}'. You have to analyze patient information and guidelines to answer the question.
    Keep your answer ground in the facts of the retrieved symptoms.
    If the retrieved symptoms doesn't contain the facts to answer the QUESTION return like this- 'there are no relevant Syntrillo expert recommendations for this patient'
    IMPORTANT: Do not include any introductory or summarizing statements. Start immediately with numbered recommendations.
    """
    return model_invoke(prompt_template, model)


def get_answer_guideline(question, context, collection_name, model):
    prompt_template = f"""You are a helpful assistant that answers questions directly and only using the information provided in the context below.

    Guidance for answers:
        - Always use English as the language in your responses.
        - In your answers, always use a professional tone.
        - If the context does not contain the answer, say "answer not found."
        - IMPORTANT: Do not include any introductory or summarizing statements. Start immediately with numbered recommendations.
    Now read this context below and answer the question at the bottom.

    ***Context:
    {context}

    ***Question:
    {question}

    **INSTRUCTIONS**
    Answer the user QUESTION ONLY using the DOCUMENT Context as a reference. These documents are retrieved from '{collection_name}'. You have to analyze patient information and guidelines to answer the question.
    Keep your answer ground in the facts of the retrieved guidelines.
    If the retrieved guidelines doesn't contain the facts to answer the QUESTION return in 3 words- 'answer not found'
    IMPORTANT: Do not include any introductory or summarizing statements. Start immediately with numbered recommendations.
    """
    return model_invoke(prompt_template, model)



def process_query(query, collection_name, prompt_name, context, model):
    if prompt_name == "guideline":
        answer = get_answer_guideline(query, context, collection_name, model)
    elif prompt_name == "symptom":
        answer = get_answer_symptoms(query, context, collection_name, model)
    else:
        raise ValueError("Unsupported prompt name")
    return answer


def get_final_answer(query, model):
    query_text_guideline = "This is the patient's information- " +  query + " What American Heart Association recommendations apply to this patient? Please only include recommendations associated with level A and level B evidence"
    query_text_symptoms = "This is the patient's information- " +  query + " What are some things our experts would recommend to the patient based on their main neurological symptoms or issues they are concerned with? Limit to one paragraph or 5 bullet points depending on the response."
    collection_names = ["stroke_prevention", "virtual_care_expert_answers"]
    prompt_names = ["guideline", "symptom"]
    answers = []
    for collection_name, query, prompt_name in zip(collection_names, [query_text_guideline, query_text_symptoms], prompt_names):
        db = initialize_db(collection_name)
        similar_docs = get_similar_docs(db, query, k=8)
        context = "\n\n".join([doc[0].page_content for doc in similar_docs])
        answer = process_query(query, collection_name, prompt_name, context, model)
        answers.append(answer)
    final_answer = f"""GUIDELINES BASED CLINICAL RECOMMENDATIONS
    {answers[0]}
    \n\n\n
    SYNTRILLO EXPERT SUGGESTIONS FOR PATIENT CONCERNS
    {answers[1]}"""
    return final_answer