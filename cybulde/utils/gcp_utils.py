from google.cloud import secretmanager


def access_secret_version(project_id: str, secret_id: str, version_id: str = "1") -> str:
    """
    Access the payload for the given secret version if one exists.
    The version can be a version number as string (e.g. "5") or an alias (e.g. "latest")
    """
    # Creating a secretmanager clien object
    client = secretmanager.SecretManagerServiceClient()
    # Name of the resource we would like to get
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    # Payload of the response
    payload = response.payload.data.decode("UTF-8")
    return payload

