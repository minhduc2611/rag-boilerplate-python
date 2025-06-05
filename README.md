
# Create a new virtual environment
```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


# Test Locally

```
func start
```

# Create a new function
```
func new --template "HTTP trigger" --name <function-name>
```

# Install dependencies
```
pip install <package-name>
```

# Freeze dependencies
```
pip freeze > requirements.txt
```
