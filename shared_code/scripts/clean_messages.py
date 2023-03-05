import os
os.environ["AzureStorageConnectionString"]="DefaultEndpointsProtocol=https;AccountName=ajdevreddit;AccountKey=+9066TCgdeVignRdy50G4qjmNoUJuibl9ERiTGzdV4fwkvgdV3aSVqgLwldgZxj/UpKLkkfXg+3k+AStjFI33Q==;BlobEndpoint=https://ajdevreddit.blob.core.windows.net/;QueueEndpoint=https://ajdevreddit.queue.core.windows.net/;TableEndpoint=https://ajdevreddit.table.core.windows.net/;FileEndpoint=https://ajdevreddit.file.core.windows.net/;"
if __name__ == '__main__':
	from dotenv import load_dotenv
	from shared_code.messaging.message_sender import MessageBroker

	load_dotenv()
	broker = MessageBroker()
	for i in range(0, 250):
		m = broker.get_message("message-generator")
		broker.delete_message("message-generator", m)
	exit(0)