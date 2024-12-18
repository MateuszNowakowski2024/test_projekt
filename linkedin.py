import requests
import json
from os import path
from utils import custom_print, get_content_type, get_file_data, MEDIA_CATEGORY
from re import sub
import re

class ContentTooLong(requests.RequestException):
    """ LinkedIn post limit reached """
    pass


class LinkedIn:
    POST_CHAR_LIMIT     = 3000

    BASE_URL            = "https://www.linkedin.com"

    POST_ENDPOINT       = BASE_URL + "/voyager/api/contentcreation/normShares"
    UPLOAD_ENDPOINT     = BASE_URL + "/voyager/api/voyagerVideoDashMediaUploadMetadata?action=upload"

    def __init__(self, cookies, config_fname='../config.json'):
        self.config_fname = config_fname
        self.cookies      = { key: value.strip() if isinstance(value, str) else value for key, value in cookies.items() }

        if '\"' in cookies["JSESSIONID"]:
            self.cookies["JSESSIONID"] = sub( r'\"+', '', cookies["JSESSIONID"] )

        self.headers = {
            "accept"            : "application/vnd.linkedin.normalized+json+2.1",
            "accept-language"   : "en-US,en;q=0.9",
            "content-type"      : "application/json; charset=UTF-8",
            "csrf-token"        : self.cookies["JSESSIONID"],
            "origin"            : self.BASE_URL,
            "cookie"            : '; '.join([f'{key}="{value}"' if key == "JSESSIONID" else f'{key}={value}' for key, value in self.cookies.items()]),
            "Referer"           : self.BASE_URL + "/feed/",
            "Referrer-Policy"   : "strict-origin-when-cross-origin, strict-origin-when-cross-origin",
            "User-Agent"        : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
            # ... other headers ...
        }

        self.member_id = ''

    def update_cookies(self):
        # Update the cookies in the headers
        self.headers["cookie"] = '; '.join(
            [f'{key}="{value}"' if key == "JSESSIONID" else f'{key}={value}' for key, value in self.cookies.items()])

        # Update the cookies in the config file
        dir_path    = path.dirname(path.realpath(__file__))   # Gets the directory where the script is located
        config_path = path.join(dir_path, self.config_fname)  # Constructs the path to the config file
        try:
            with open(config_path, 'r') as file:
                config = json.load(file)

            config['cookies'] = self.cookies

            with open(config_path, 'w') as file:
                json.dump(config, file, indent=4)

            print("Cookies updated in config file.")

        except (FileNotFoundError, IOError) as e:
            print(f"Error updating config file: {e}")

    def check_session(self, resp_headers=None ):
        try:
            if not resp_headers:
                response = requests.get(self.BASE_URL, headers=self.headers)
                response.raise_for_status()

                resp_headers = response.headers

            if "Set-Cookie" in resp_headers and "li_at=" in resp_headers['Set-Cookie']:

                cookie_parts  = resp_headers['Set-Cookie'].split(';')
                has_updates   = False

                for cookie_key in [
                    "JSESSIONID",
                    "li_at"
                ]:
                    if f"{cookie_key}=" in resp_headers['Set-Cookie']:
                        # Extracting the cookie value
                        found_cookie = next( ( part for part in cookie_parts if f"{cookie_key}=" in part ), None)

                        if found_cookie:

                            # Extract the value
                            new_cookie_value = found_cookie.split(f"{cookie_key}=")[1].split(';')[0].strip().replace('\"', '')

                            if new_cookie_value and self.cookies[cookie_key] != new_cookie_value:
                                # Update the configuration with the new cookie
                                self.cookies[cookie_key] = new_cookie_value
                                has_updates = True

                if has_updates:
                    self.update_cookies()

        except requests.exceptions.RequestException as e:
            custom_print(f"Error checking LinkedIn session: {e}")

    # def get_recent_posts(self, count=1):
    #     get_posts_endpoint = self.BASE_URL + "/voyager/api/graphql?variables=" \
    #                                          "(count:" + str(count) + ",start:0,profileUrn:" + self.member_id + ")" \
    #                                          "&queryId=voyagerFeedDashProfileUpdates.d50d324a655e6bbeff4e0490ffde19d1"
    #
    #     try:
    #         response = requests.get(get_posts_endpoint, headers=self.headers)
    #
    #         response.raise_for_status()
    #         # Handle response
    #
    #         self.check_session(response.headers)
    #
    #     except requests.exceptions.RequestException as e:
    #         custom_print(f"Error retrieving recent LinkedIn posts: {e}")

    def post(self, text, media=None):

        if media is None:
            media = []

        payload = {
            "visibleToConnectionsOnly": False,
            "externalAudienceProviders": [],
            "commentaryV2": {
                "text": text,
                "attributes": []
            },
            "origin": "FEED",
            "allowedCommentersScope": "ALL",
            "postState": "PUBLISHED",
            "media": media
        }

        try:

            if len(text) > self.POST_CHAR_LIMIT:
                raise ContentTooLong()

            response = requests.post(self.POST_ENDPOINT, headers=self.headers, json=payload)

            response.raise_for_status()
            # Handle response

            self.check_session(response.headers)

        except ContentTooLong:
            custom_print(f"Error posting to LinkedIn: post character limit reached")
        except requests.exceptions.RequestException as e:
            custom_print(f"Error posting to LinkedIn: {e}")

    def post_file(self, text, file_path_list=None):

        # TODO: find all mediaUploadType's. Determine use-case. Store in fs or stream?

        if file_path_list is None:
            file_path_list = []

        file_path = path.join(*file_path_list)

        fname = file_path_list[-1]
        fbinary, fsize, ftype = get_file_data( file_path, protocol="rb", incl_meta=True )

        payload = {
            "mediaUploadType": "IMAGE_SHARING",
            "fileSize": fsize,
            "filename": fname
        }

        content_type = get_content_type(file_path)

        if not content_type:
            return

        try:
            response = requests.post(self.UPLOAD_ENDPOINT, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()

            self.check_session(response.headers)

            data                              = response.json()["data"]["value"]
            upload_endpoint                   = data["singleUploadUrl"]
            self.headers["media-type-family"] = data["singleUploadHeaders"]["media-type-family"]
            self.headers["content-type"]      = content_type

            response = requests.put(upload_endpoint, headers=self.headers, data=open(file_path, 'rb'))
            response.raise_for_status()

            # image is uploaded. now post.
            self.post(
                text,
                [
                    # video category has different keys
                    { "category": MEDIA_CATEGORY.IMAGE.name, "mediaUrn": data["urn"], "tapTargets": [] }
                ]
            )

        except requests.exceptions.RequestException as e:
            custom_print(f"Error posting to LinkedIn: {e}")
            
            
def login_linkedin(username, password):
    """
    Log in to LinkedIn using username and password and return a session with appropriate cookies.
    Adjust selectors, URLs, and parameters as needed based on LinkedIn's login flow.
    """

    login_url = "https://www.linkedin.com/checkpoint/lg/login-submit"
    session = requests.Session()

    # Step 1: GET the login page to retrieve CSRF tokens and cookies
    # The login page URL may redirect or change.
    initial_url = "https://www.linkedin.com/login"
    r = session.get(initial_url, headers={
        "User-Agent"        : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Referrer-Policy"   : "strict-origin-when-cross-origin, strict-origin-when-cross-origin"
        })
    
    if r.status_code != 200:
        raise Exception(f"Failed to load login page, status code: {r.status_code}")

    # Extract the loginCsrfParam from the page
    # You need to inspect the LinkedIn login page source to find the hidden fields names
    csrf_token_pattern = re.compile(r'name="loginCsrfParam" value="([^"]+)"')
    match = csrf_token_pattern.search(r.text)
    if not match:
        raise Exception("Could not find loginCsrfParam on the login page.")
    login_csrf_param = match.group(1)

    # Step 2: POST credentials to the login-submit endpoint
    payload = {
        'session_key': username,
        'session_password': password,
        'loginCsrfParam': login_csrf_param
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.linkedin.com/login",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Attempt login
    res = session.post(login_url, data=payload, headers=headers, allow_redirects=True)
    
    if res.status_code != 200 and res.status_code != 302:
        raise Exception(f"Login request failed with status code: {res.status_code}")

    # After login, check if we are indeed logged in by checking for cookies
    li_at = session.cookies.get('li_at')
    jsessionid = session.cookies.get('JSESSIONID')

    if not li_at or not jsessionid:
        # If we didn't get these cookies, it likely means the login failed.
        # You may want to print res.text or inspect further.
        raise Exception("Failed to retrieve li_at or JSESSIONID cookies. Possibly incorrect credentials or changed login flow.")

    print("Logged in successfully. Retrieved cookies:")
    print("li_at:", li_at[-3:])
    print("JSESSIONID:", jsessionid[-3:])

    return session  
