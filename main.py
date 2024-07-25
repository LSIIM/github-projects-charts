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

class Card:
    def __init__(self, id, title, assignees, status_name, status_updatedAt, iteration_id, iteration_end, estimate_hours, prioriority, impact):
        self.id = str(id)
        self.title = str(title)
        if isinstance(assignees, list):
            self.assignees = [str(assignee["login"]) for assignee in assignees]
        else:
            self.assignees = [str(assignees)]
        self.status_name = str(status_name)

        # check if status_updatedAt is a valid datetime obj
        if isinstance(status_updatedAt, datetime):
            self.status_updatedAt = status_updatedAt
        else:
            raise ValueError(f"status_updatedAt must be a datetime object: {status_updatedAt}")
        self.iteration_id = str(iteration_id)
        if isinstance(iteration_end, datetime):
            self.iteration_end = iteration_end
        else:
            raise ValueError(f"iteration_end must be a datetime object: {iteration_end}")
        if isinstance(estimate_hours, (int, float)):
            self.estimate_hours = str(estimate_hours)
        else:
            self.estimate_hours = 0 # no estimate yet
        self.prioriority = str(prioriority)
        self.impact = str(impact)

    def __str__(self):
        return f"Card: {self.id}\n" + \
               f"  Título: {self.title}\n" + \
               f"  Assignees: {', '.join(self.assignees) if self.assignees else 'Nenhum'}\n" + \
               f"  Status: {self.status_name} (Atualizado em: {self.status_updatedAt.strftime('%Y-%m-%d %H:%M:%S')})\n" + \
               f"  Iteração: {self.iteration_id} (Término: {self.iteration_end.strftime('%Y-%m-%d')})\n" + \
               f"  Estimativa (Horas): {self.estimate_hours}\n" + \
               f"  Prioridade: {self.prioriority}\n" + \
               f"  Impacto: {self.impact}"


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
    cards = []
    # pprint(result)
    items = result["data"]["node"]["items"]["nodes"]
    for item in items:
        content = item.get("content")
        card_data = {
            "id": None,
            "title": None,
            "assignees": [],
            "status_name": None,
            "status_updatedAt": None,
            "iteration_id": None,
            "iteration_end": None,
            "estimate_hours": None,
            "prioriority": None,
            "impact": None

        }
        if content:
            title = content.get("title", "Sem título")
            card_data["title"] = title
            # print(f" - Item ID: {item['id']}, Título: {title}")
            assignees = content.get("assignees", {}).get("nodes", [])
            assignee_logins = [assignee['login'] for assignee in assignees]
            # print(f"    Assignees: {', '.join(assignee_logins) if assignee_logins else 'Nenhum'}")
        
        field_values = item.get("fieldValues", {}).get("nodes", [])
        for field in field_values:
            field_name = field.get("field", {}).get("name", "Desconhecido")
            field_value = field.get("text") or field.get("date") or field.get("name") or field.get("number") or "Sem valor"

            if field_name == "Status":
                card_data["status_name"] = field.get('name')
                card_data["status_updatedAt"] = datetime.strptime(field.get('updatedAt'), "%Y-%m-%dT%H:%M:%SZ")

            if "iterationId" in field:
                field_value = f"{field.get('title')} (Início: {field.get('startDate')}, Duração: {field.get('duration')} dias, "
                start_datetime = datetime.strptime(field.get('startDate'), "%Y-%m-%d")
                end_datetime = start_datetime + timedelta(days=field.get('duration'))
                field_value += f"Término: {end_datetime.strftime('%Y-%m-%d')})"
                card_data["iteration_id"] = field.get('iterationId')
                card_data["iteration_end"] = end_datetime
            if "users" in field:
                field_value = "(" + ", ".join([user['login'] for user in field.get('users', {}).get('nodes', [])]) +")"
                card_data["assignees"] = field.get('users', {}).get('nodes', [])
            if field_name == "Estimate (Hours)":
                card_data["estimate_hours"] = field_value

            # print(f"    Campo: {field_name}, Valor: {field_value}")
            # pprint(card_data)
        cards.append(Card(**card_data))
    return cards

if __name__ == '__main__':
    cards = list_project_cards(PROJECT_ID)
    for card in cards:
        print(card)
