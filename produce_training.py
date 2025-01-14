import json

logger_path = 'logger path'
tool_path = 'tool path'

def read_file(file_path):
    datas = []
    with open(file_path, 'r') as file:
        for line in file:
            datas.append(json.loads(line))
    return datas

logger = read_file(logger_path)
tools = []
chains = []

for entry in logger:
    if entry['type'] == 'tool':
        tools.append(entry)
    if entry['type'] == 'chain':
        chains.append(entry)

tool_description = read_file(tool_path)[0]


dataset = []
for tool in tools:
    query = tool.get('query')
    tool_name = tool.get('tool_name')
    for tool_d in tool_description:
        if tool_d.get('tool_name') == tool_name:
            description = tool_d['description']
            args = tool_d['args']
    tool_input = tool['input']
    dataset.append({
        "query":query,
        "tool_name":tool_name,
        "description":description,
        "args":args,
        "tool_input":tool_input
    })


def transorm_data(input_data):
    transform_data = []
    
    for idx,data in enumerate(input_data):
        query = data['query']
        tool_name = data['tool_name']
        description = data['description'],
        args = data['args']
        tool_input= json.loads(data['tool_input'].replace("'", "\""))
        for key,value in args.items():
            if 'title' in value:
                del value['title']
        transformed_query = {
            "query":query,
            "id":idx,
            "answers":json.dumps([{
                "name":tool_name,
                "arguments":tool_input
            }]),
            "tools":json.dumps([{   
                "name":tool_name,
                "description":description,
                "parameters":args
            }])
        }
        transform_data.append(transformed_query)
    return transform_data

transformed_data = transorm_data(dataset)

chain_dataset = []
i = len(transformed_data)
for chain in chains:
    
    if chain.get('inputs'):
        chain_dataset.append({
            "query":chain['prompt'][0][7:],
            "id":i,
            "answer":json.dumps([chain['outputs']])
        })
    i+=1
transformed_data.extend(chain_dataset)

for data in transformed_data:
    print("\n\n",data)