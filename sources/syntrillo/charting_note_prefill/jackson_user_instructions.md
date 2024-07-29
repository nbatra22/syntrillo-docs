# Jackson's charting note prefill instructions for users

The program will gather information from the patients hospital discharge uploaded on healthie in order to prefill questions for forms on healthie. Intstructions for the AI should be provided under the LLM prompt column of the spread sheet.

For any questions you don't want the AI to prefill leave the box empty.

You can use "auto" as the llm prompt to ask the AI the exact same question provided on the form. This is designed for very basic questions like identifing a single object like the patients age but can struggle with more complicated tasks due to lack of background information or response formating.

When constructing a prompt it can help to break the instructions down into simple steps for the AI to follow allow with providing a template for the json output. Some examples are provided below.

*  Follow the steps provided. Step 1: Find the patient's physical examination. Step 2: From the physical examination, identify all of the patient's recent blood pressure measurements. Step 3: Average the values of the patient's blood pressure measurements. When averaging blood pressure, calculate the average of the numerators and denominators separately and return your response as “average numerator/average denominator”. Step 4: Return a dictionary in the following format: {'average_blood_pressure': }

*  What is the hospital's address. Respond with a dictionary in the following format: {'address': }

The name used for the dictionary won't be included in the forms prefill. This just helps prevent the AI from splitting up the answer into to segments. Example: {'street': , 'city': , 'state': , 'zip code': } instead of the address format above.
