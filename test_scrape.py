from shared_code.clients import push_shift_client
from shared_code.clients.push_shift_client import PushShiftClient


def main():
	client: PushShiftClient = PushShiftClient()
	data = client.get_author_comments("ReallyRickAstley")
	i = 0
	for comment in data:
		result = client.handle_comment(comment)
		print(result.__dict__)
		i += 1


if __name__ == '__main__':
	main()
