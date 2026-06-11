# API Coverage By Swagger 

## Launch 

1. install poetry: <https://python-poetry.org/docs/>
2. install task: <https://taskfile.dev/installation/>
3. ```task install-deps```
4. ```task run```
5. open <http://127.0.0.1:8000> 

## Usage

Inside the project, in the example directory, there is an example of a simple FastAPI application and API tests for it, which demonstrate how the tool works.

### Run app example 
1. ```task example```
2. open <http://127.0.0.1:8080> 

### Integration
1. By UI - <http://127.0.0.1:8000/>
2. By API - <http://127.0.0.1:8000/docs> 

### Integration By UI:
2. open <http://127.0.0.1:8000> 
3. In the **Base URL** field, enter ```http://127.0.0.1:8080```
4. In the **JSON Schema URL** field, enter ```http://127.0.0.1:8080/openapi.json```
5. Run the tests with the command ```poetry run pytest example --alluredir=allure-results```
6. Refresh the tool page at <http://127.0.0.1:8000>

## Screenshots

![URL form](/assets/url_form.png)

![First view](/assets/first_view.png)

![Covered endpoint on the "Covered" tab](/assets/covered_endpoint.png)

![Simple test example](/assets/simple_test_example.png)