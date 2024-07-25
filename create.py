import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PROJECT_ID = "PVT_kwDOBtcSac4Ak0uo"  # ID do projeto AgroSmart
ASSIGNEE = "CodeWracker"

"""
[{'field': {'id': 'PVTF_lADOBtcSac4Ak0uozgc-NWE',
            'name': 'Assignees'},
'users': {'nodes': [{'login': 'CodeWracker'},
                    {'login': 'Fabioomega'}]}},
{'field': {'id': 'PVTF_lADOBtcSac4Ak0uozgc-NWA',
            'name': 'Title'},
'text': 'sss'},
{'field': {'id': 'PVTSSF_lADOBtcSac4Ak0uozgc-NWI',
            'name': 'Status'},
'name': 'Backlog'},
{'field': {'id': 'PVTSSF_lADOBtcSac4Ak0uozgc-NYY',
            'name': 'Priority'},
'name': 'P0'},
{'duration': 14,
'field': {'id': 'PVTIF_lADOBtcSac4Ak0uozgc-NYk',
            'name': 'Iteration'},
'iterationId': '381c7c80',
'startDate': '2024-07-16',
'title': 'Iteration '
        '1'},
{'field': {'id': 'PVTSSF_lADOBtcSac4Ak0uozgc-NYc',
            'name': 'Size'},
'name': 'XS'},
{'field': {'id': 'PVTF_lADOBtcSac4Ak0uozgc-NYg',
            'name': 'Estimate'},
'number': 10.0}]
"""

ASSIGNEES_COLUMN_ID = "PVTF_lADOBtcSac4Ak0uozgc-NWE"
TITLE_COLUMN_ID = "PVTF_lADOBtcSac4Ak0uozgc-NWA"
STATUS_COLUMN_ID = "PVTSSF_lADOBtcSac4Ak0uozgc-NWI"
PRIORITY_COLUMN_ID = "PVTSSF_lADOBtcSac4Ak0uozgc-NYY"
ITERATION_COLUMN_ID = "PVTIF_lADOBtcSac4Ak0uozgc-NYk"
SIZE_COLUMN_ID = "PVTSSF_lADOBtcSac4Ak0uozgc-NYc"
ESTIMATE_COLUMN_ID = "PVTF_lADOBtcSac4Ak0uozgc-NYg"

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

def get_user_id(username):
    query = '''
    query($username: String!) {
        user(login: $username) {
            id
        }
    }
    '''
    variables = {"username": username}
    result = run_query(query, variables)
    print(f'User ID: {result}')
    return result["data"]["user"]["id"]

def create_project_card(project_id, column_id, note):
    query = '''
    mutation($projectId: ID!, $columnId: ID!, $note: String!) {
        addProjectCard(input: {projectColumnId: $columnId, note: $note}) {
            projectColumn {
                id
            }
            cardEdge {
                node {
                    id
                }
            }
        }
    }
    '''
    variables = {
        "projectId": project_id,
        "columnId": column_id,
        "note": note
    }
    result = run_query(query, variables)
    print(result)
    return result["data"]["addProjectCard"]["cardEdge"]["node"]["id"]

def add_assignee_to_card(card_id, assignee_id):
    query = '''
    mutation($cardId: ID!, $assigneeId: ID!) {
        addAssigneesToAssignable(input: {assignableId: $cardId, assigneeIds: [$assigneeId]}) {
            assignable {
                ... on Issue {
                    id
                }
                ... on PullRequest {
                    id
                }
            }
        }
    }
    '''
    variables = {
        "cardId": card_id,
        "assigneeId": assignee_id
    }
    run_query(query, variables)

def set_iteration_for_card(card_id, iteration_field_id, start_date, duration):
    query = '''
    mutation($cardId: ID!, $fieldId: ID!, $startDate: Date!, $duration: Int!) {
        updateProjectV2ItemFieldValue(input: {projectId: $cardId, fieldId: $fieldId, value: {iterationId: {startDate: $startDate, duration: $duration}}}) {
            projectV2Item {
                id
            }
        }
    }
    '''
    variables = {
        "cardId": card_id,
        "fieldId": iteration_field_id,
        "startDate": start_date,
        "duration": duration
    }
    run_query(query, variables)

if __name__ == '__main__':
    assignee_id = get_user_id(ASSIGNEE)
    card_id = create_project_card(PROJECT_ID, COLUMN_ID, "teste graphql")
    add_assignee_to_card(card_id, assignee_id)

    # Adicione a iteração atual ao card
    # Substitua estas variáveis com as informações corretas da iteração
    start_date = "2024-07-20"  # Substitua com a data de início correta
    duration = 14  # Substitua com a duração correta em dias
    set_iteration_for_card(card_id, ITERATION_FIELD_ID, start_date, duration)

    print(f"Card criado e atribuído a {ASSIGNEE} na iteração atual")
