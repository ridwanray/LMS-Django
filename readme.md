# Create a .env file by copying the .env.sample provided

## run `docker-compose build`

## run `docker-compose up`

## run  `docker-compose up -f docker-compose.dev.yml up --build` as an alternative



# Run tests
Run descriptive tests in the container
```
docker-compose exec api pytest -n auto -rP -vv 
```


Access the doc on

```
localhost:8000/api/v1/doc
```

