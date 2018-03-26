Example Alexa voice interface for Mojo WiFi using the APIs
This is a proof of concept code on how to create a voice interface using Alexa Skills kit API and the Mojo Cloud API. This repo contains the backend for the example Skill with a couple of voice commands: a) status of network at a location b) start a live network test using 3rd radio and reply back with results. The backend Python code is Python 2.7 compatible and can be hosted in Amazon Lambda. The Alexa Skills kit developer console has to be used to create the intents and link them to the lambda service hosting this Python code. When the user invokes a voice command the Alexa framework generates the intent and invokes the lambda function along with the slots. The Python code fulfills the intents by making API calls to Mojo cloud to fetch data and generating text reponse that will be read by out Alexa device (E.g. Echo dot). 

#Getting Started
1. Checkout the Python code and make any changes
2. Program the correct API keys to point to the desired Mojo cloud instance.
3. Create a new AWS lambda function and upload the Python code
4. Create Amazon developer account
5. Create a new skill from the Skills Kit console and configure intents and slots.
6. Configure the intent fulfilment to point to the lambda function
7. Test using a Alexa capable device by invoking the voice commands configured in step 5 above. 

NOTE: The logs from the lambda function (Python code uploaded) will be available at AWS cloudwatch service. This can be used for debugging purpose.

#Prerequisites
1. AWS service account
2. AWS developer account
3. Python coding skills
4. Alexa capable device (E.g. Echo dot)

#Running the tests
Invoke the skill and utter the voice commands through an Alexa capable device like echo dot. Use CloudWatch to check logs from the lambda function for debugging.

#License
This project is licensed under the Mojo Products and Services License Agreement(https://www.mojonetworks.com/products-and-services-license-agreement)

