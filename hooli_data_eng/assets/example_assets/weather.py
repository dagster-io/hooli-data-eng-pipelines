#from pydantic import PrivateAttr
#from typing import Any, Dict
#
#from dagster import asset, ConfigurableResource, Definitions, Field
#from google.oauth2 import service_account
#from googleapiclient.discovery import build
#
#
#class GoogleSheetsResource(ConfigurableResource):
#    credentials_file: str = "/Users/izzy/Downloads/google_credentials.json"
#    spreadsheet_id: str = "1Qlp3HVaJd0PHvb546rA0SgqtMsTO56Yp5fPWm6M04YU"
#    scopes: list[str] = ["https://www.googleapis.com/auth/spreadsheets"]
#    _service: Any = PrivateAttr(default=None)
#    
#    def setup_resource(self):
#        """Initialize the Google Sheets service."""
#        credentials = service_account.Credentials.from_service_account_file(
#            self.credentials_file,
#            scopes=self.scopes
#        )
#        self._service = build('sheets', 'v4', credentials=credentials)
#    
#    def get_values(self, range_name: str) -> Dict:
#        """Read values from a Google Sheet."""
#        result = self._service.spreadsheets().values().get(
#            spreadsheetId=self.spreadsheet_id,
#            range=range_name
#        ).execute()
#        return result
#    
#    def update_values(self, range_name: str, values: list) -> Dict:
#        """Write values to a Google Sheet."""
#        body = {"values": values}
#        result = self._service.spreadsheets().values().update(
#            spreadsheetId=self.spreadsheet_id,
#            range=range_name,
#            valueInputOption="USER_ENTERED",
#            body=body
#        ).execute()
#        return result
#    
#
## Define the resource
#google_sheets_resource = GoogleSheetsResource()
#
#
#@asset(
#    config_schema={"range": Field(str, default_value="A1:B6")}
#)
#def get_lat_long(context, google_sheets: GoogleSheetsResource) -> Dict:
#    """
#    Reads a Google sheet and returns values as a dictionary
#    """
#    # Get range from asset config
#    range_value = context.op_config["range"]
#    
#    # Use the resource's method to get values
#    result = google_sheets.get_values(range_value)
#    
#    # Log the result for debugging
#    context.log.info(f"Read data: {result}")
#    
#    return result
#
#
## Define the Dagster Definitions
#defs = Definitions(
#    assets=[get_lat_long],
#    resources={"google_sheets": google_sheets_resource}
#)