import os
import requests
from dotenv import load_dotenv
import json
# para trabalhar com datas
from datetime import datetime, timedelta
from pprint import pprint
import pandas as pd
import numpy as np
import plotly.express as px

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
        if isinstance(iteration_end, datetime) or iteration_end is None:
            self.iteration_end = iteration_end
        else:
            raise ValueError(f"iteration_end must be a datetime object or None: {iteration_end}")
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
    cards = []
    has_next_page = True
    end_cursor = None  # Início sem cursor

    while has_next_page:
        query = '''
        query($projectId: ID!, $cursor: String) { 
            node(id: $projectId) {
                ... on ProjectV2 {
                    items(first: 20, after: $cursor) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
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
                                        users(first: 100) {
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
                                    assignees(first: 100) {
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
        variables = {"projectId": project_id, "cursor": end_cursor}
        result = run_query(query, variables)
        # pprint(result)
        if 'errors' in result:
            raise Exception(f"GraphQL Error: {result['errors']}")
        
        items = result.get("data", {}).get("node", {}).get("items", {}).get("nodes", [])
        page_info = result.get("data", {}).get("node", {}).get("items", {}).get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        end_cursor = page_info.get("endCursor")
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
                    # print(content)
                if "users" in field:
                    field_value = "(" + ", ".join([user['login'] for user in field.get('users', {}).get('nodes', [])]) +")"
                    card_data["assignees"] = field.get('users', {}).get('nodes', [])
                if field_name == "Estimate (Hours)":
                    card_data["estimate_hours"] = field_value

                # print(f"    Campo: {field_name}, Valor: {field_value}")
                # pprint(card_data)
            cards.append(Card(**card_data))
    return cards


def create_burndown_chart(cards):
    df = pd.DataFrame([card.__dict__ for card in cards])
    df["status_updatedAt"] = pd.to_datetime(df["status_updatedAt"])
    df["iteration_end"] = pd.to_datetime(df["iteration_end"])
    df["estimate_hours"] = pd.to_numeric(df["estimate_hours"])
    
    # plot a line chart with the burndown
    # line 1: x = iteration_end, y = estimate_hours (sum cumulatively)
    # line 2: x = status_updatedAt (if status_name is "Done"), y = estimate_hours (sum cumulatively)

    # create a new dataframe with the burndown data
    burndown_data = []
    for item in df.iterrows():
        row = item[1]
        iteration_end = row["iteration_end"]
        status_name = row["status_name"]
        status_updatedAt = row["status_updatedAt"]
        # get only date part, ignore time
        status_updatedAt = status_updatedAt.replace(hour=0, minute=0, second=0, microsecond=0)
        estimate_hours = row["estimate_hours"]
        estimate_hours_status = estimate_hours if status_name == "Done" else 0
    
        burndown_data.append({
            "iteration_end": iteration_end,
            "status_updatedAt": status_updatedAt,
            "estimate_hours": estimate_hours,
            "estimate_hours_status": estimate_hours_status
        })
    burndown_df = pd.DataFrame(burndown_data)

    iter_data = pd.DataFrame()
    iter_data['iteration_end'] = burndown_df['iteration_end']
    iter_data['estimate_hours'] = burndown_df['estimate_hours']
    # group by iteration_end and sum the estimate_hours
    iter_data = iter_data.groupby('iteration_end').sum().reset_index()

    # ------
    # DROP THE FIRST LINE BECAUSE IT WAS BEING TRACKED IN JIRA AND MOVED TO GITHUB, SO IT WAS NOT POSSIBLE TO UPDATE THE STATUS IN THE PAST
    # iter_data = iter_data.iloc[1:]
    # ------
    # sum cumulatively
    iter_data['estimate_hours'] = iter_data['estimate_hours'].cumsum()


    status_data = pd.DataFrame()
    status_data['status_updatedAt'] = burndown_df['status_updatedAt']
    status_data['estimate_hours_status'] = burndown_df['estimate_hours_status']
    # group by status_updatedAt and sum the estimate_hours_status
    status_data = status_data.groupby('status_updatedAt').sum().reset_index()
    # sum cumulatively
    status_data['estimate_hours_status'] = status_data['estimate_hours_status'].cumsum()

    print(iter_data)
    print(status_data)

    fig = px.line(title='Burndown Chart', labels={'iteration_end':'Iteration End', 'estimate_hours':'Estimate Hours'}, template='plotly_dark')
    fig.add_scatter(x=iter_data['iteration_end'], y=iter_data['estimate_hours'], mode='lines', name='Estimate Hours')
    fig.add_scatter(x=status_data['status_updatedAt'], y=status_data['estimate_hours_status'], mode='lines', name='Done')
    
    # save the chart as a file
    if not os.path.exists("burndown_charts"):
        os.makedirs("burndown_charts")
    today_date = datetime.now().strftime("%Y-%m-%d")
    chart_filename = f"burndown_charts/burndown_chart_{today_date}.png"
    fig.write_image(chart_filename, height=1000, width=2000)


        

    


if __name__ == '__main__':
    cards = list_project_cards(PROJECT_ID)
    # for card in cards:
    #     if card.status_name == "Done":
    #         print(card)
    
    create_burndown_chart(cards)
    

