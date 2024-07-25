import os
import requests
from dotenv import load_dotenv
import json
# para trabalhar com datas
from datetime import datetime, timedelta
from pprint import pprint

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PROJECT_ID = os.getenv('PROJECT_ID') # ID do projeto AgroSmart

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}


def run_query(query, variables=None):
    request = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(f"Query failed with status code {request.status_code}. {request.json()}")

def list_project_cards(project_id):
    query = '''
    query($projectId: ID!) {
        node(id: $projectId) {
            ... on ProjectV2 {
                items(first: 20) {
                    nodes {
                        id
                        fieldValues(first: 20) {
                            nodes {
                                ... on ProjectV2ItemFieldTextValue {
                                    text
                                    field {
                                        ... on ProjectV2FieldCommon {
                                            name
                                            id
                                        }
                                    }
                                }
                                ... on ProjectV2ItemFieldDateValue {
                                    date
                                    field {
                                        ... on ProjectV2FieldCommon {
                                            name
                                            id
                                        }
                                    }
                                }
                                ... on ProjectV2ItemFieldSingleSelectValue {
                                    name
                                    updatedAt
                                    field {
                                        ... on ProjectV2FieldCommon {
                                            name
                                            updatedAt
                                            id
                                        }
                                    }
                                }
                                ... on ProjectV2ItemFieldNumberValue {
                                    number
                                    field {
                                        ... on ProjectV2FieldCommon {
                                            name
                                            id
                                        }
                                    }
                                }
                                ... on ProjectV2ItemFieldIterationValue {
                                    iterationId
                                    startDate
                                    duration 
                                    title
                                    field {
                                        ... on ProjectV2FieldCommon {
                                            name
                                            id
                                        }
                                    }
                                }
                                ... on ProjectV2ItemFieldUserValue {
                                    users(first: 10) {
                                        nodes {
                                            login 
                                        }
                                    }
                                    field {
                                        ... on ProjectV2FieldCommon {
                                            name
                                            id
                                        }
                                    }
                                }
                            }
                        }
                        content {
                            ... on DraftIssue {
                                title
                                body
                            }
                            ... on Issue {
                                title
                                assignees(first: 10) {
                                    nodes {
                                        login
                                    }
                                }
                            }
                            ... on PullRequest {
                                title
                                assignees(first: 10) {
                                    nodes {
                                        login
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    '''
    variables = {"projectId": project_id}
    result = run_query(query, variables)
    pprint(result)
    items = result["data"]["node"]["items"]["nodes"]
    for item in items:
        content = item.get("content")
        if content:
            title = content.get("title", "Sem título")
            print(f" - Item ID: {item['id']}, Título: {title}")
            assignees = content.get("assignees", {}).get("nodes", [])
            assignee_logins = [assignee['login'] for assignee in assignees]
            print(f"    Assignees: {', '.join(assignee_logins) if assignee_logins else 'Nenhum'}")
        
        field_values = item.get("fieldValues", {}).get("nodes", [])
        for field in field_values:
            field_name = field.get("field", {}).get("name", "Desconhecido")
            field_value = field.get("text") or field.get("date") or field.get("name") or field.get("number") or "Sem valor"

            if field_name == "Status":
                field_value = f"{field.get('name')} (Atualizado em: {field.get('updatedAt')})"

            if "iterationId" in field:
                field_value = f"{field.get('title')} (Início: {field.get('startDate')}, Duração: {field.get('duration')} dias, "
                start_datetime = datetime.strptime(field.get('startDate'), "%Y-%m-%d")
                end_datetime = start_datetime + timedelta(days=field.get('duration'))
                field_value += f"Término: {end_datetime.strftime('%Y-%m-%d')})"
            if "users" in field:
                field_value = "(" + ", ".join([user['login'] for user in field.get('users', {}).get('nodes', [])]) +")"

             

            print(f"    Campo: {field_name}, Valor: {field_value}")

if __name__ == '__main__':
    list_project_cards(PROJECT_ID)
