# API

GET `/api/hardware`

GET `/api/accelerators`

GET `/api/models`

POST `/api/models/download` body `{model_id}`

GET `/api/models/download/status/{task_id}`

POST `/api/models/download/pause` body `{task_id}`

POST `/api/models/download/resume` body `{task_id}`

POST `/api/models/quantize` body `{model_id, mode, device, config}`

GET `/api/models/quantize/status/{job_id}`

DELETE `/api/models` body `{model_id}`

POST `/api/chat` body `{model_id, prompt, device, max_new_tokens}`