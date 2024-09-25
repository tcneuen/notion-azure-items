import configparser
from datetime import datetime

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from notion_client import Client

config = configparser.ConfigParser()
config.read("config.ini")
AZURE_ORG = config["azure"]["organization"]
AZURE_PAT = config["azure"]["personal_access_token"]
NOTION_TOKEN = config["notion"]["token"]
NOTION_DATABASE_ID = config["notion"]["database_id"]


def get_azure_work_item_data(work_item_id):
    """Fetches work item data from Azure DevOps using the API library."""

    # Create a connection to Azure DevOps
    credentials = BasicAuthentication("", AZURE_PAT)
    base_url = f"{AZURE_ORG}"
    connection = Connection(base_url=base_url, creds=credentials)

    # Get a client (the WIT client provides access to the work item tracking APIs)
    wit_client = connection.clients.get_work_item_tracking_client()

    # Get the work item
    work_item = wit_client.get_work_item(work_item_id)

    # Extract relevant fields (customize as needed)
    return {
        "Work Item ID": work_item.id,
        "Title": work_item.fields["System.Title"],
        "State": work_item.fields["System.State"],
        "AssignedTo": work_item.fields.get("System.AssignedTo", {}).get(
            "displayName", ""
        ),
        "URL": f"{AZURE_ORG}_workitems/edit/{work_item.id}",
        # Add more fields as needed
    }


def get_notion_database_items():
    """Fetches all items from the Notion database."""
    notion = Client(auth=NOTION_TOKEN)

    query_result = notion.databases.query(
        **{
            "database_id": NOTION_DATABASE_ID,
            "filter": {"property": "Synced", "checkbox": {"equals": False}},
        }
    )

    return query_result["results"]


def update_notion_database(notion_items):
    """Updates the Notion database with the given work item data, only if synced is false."""
    notion = Client(auth=NOTION_TOKEN)
    for item in notion_items:
        if (
            item["properties"]["Work Item ID"]["number"]
            and not item["properties"]["Synced"]["checkbox"]
        ):  # Assuming "Synced" is a checkbox property
            work_item_data = get_azure_work_item_data(
                item["properties"]["Work Item ID"]["number"]
            )

            new_title = (
                str(item["properties"]["Work Item ID"]["number"])
                + " - "
                + work_item_data["Title"]
            )

            print(f"Updating item: {new_title}")
            new_status = ""
            if work_item_data["State"] == "Active":
                new_status = "In progress"
            if work_item_data["State"] == "Closed":
                new_status = "Done"
            if work_item_data["State"] == "Resolved":
                new_status = "Done"
            if work_item_data["State"] == "Removed":
                new_status = "Removed"
            notion.pages.update(
                page_id=item["id"],
                properties={
                    "Synced": {"checkbox": True},
                    "Synced Date": {"date": {"start": datetime.now().isoformat()}},
                    "Name": {"title": [{"text": {"content": new_title}}]},
                    "Assigned To": {
                        "rich_text": [
                            {"text": {"content": work_item_data["AssignedTo"]}}
                        ]
                    },
                    "URL": {"url": work_item_data["URL"]},
                },
            )
            if new_status:
                notion.pages.update(
                    page_id=item["id"],
                    properties={
                        "Status": {"status": {"name": new_status}},
                    },
                )


def app():
    notion_items = get_notion_database_items()
    update_notion_database(notion_items)


if __name__ == "__main__":
    app()
