# Policy Condition Regression

Workflow: fresh `POST /documents`, then document-scoped question answering.

This is a targeted post-change check, not a full rerun of the 76-case pack. The pack is an AI-assisted self-test pack with predicted expectations, not independent ground truth.

After original claim/citation verification, qualified-policy answers preserve the complete cited policy sentence. Conditions outside that quote can still be missed. Original observations remain in `reviewer-protocol.json`.

## Fresh Upload

```json
{
  "status_code": 201,
  "seconds": 0.906,
  "body": {
    "document": {
      "id": "7b81582e25e944a1ac99f518a5b2ef8d",
      "filename": "Employee_Handbook_Test.pdf",
      "state": "READY",
      "pages": 3,
      "chunks": 3,
      "created": 1791483021.1365168,
      "error": null
    },
    "status": "READY"
  }
}
```

## R2

Question request:

```json
{
  "question": "Can I carry over unused leave?"
}
```

Predicted expectation:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Up to 5 days, to be used by 31 March.",
  "Page": "2"
}
```

Actual response and latency:

```json
{
  "status_code": 200,
  "seconds": 3.125,
  "body": {
    "status": "ANSWERED",
    "answer": "Carry-over: Up to 5 unused days may be carried into the next year and must be used by 31 March. [1]",
    "citations": [
      {
        "document_id": "7b81582e25e944a1ac99f518a5b2ef8d",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 2,
        "chunk_id": "c9bc3fcb856148129724215cc5a6af3b_1",
        "quote": "Carry-over: Up to 5 unused days may be carried into the next year and must be used by\n31 March."
      }
    ]
  }
}
```

Checks:

```json
{
  "http_200": true,
  "predicted_status": true,
  "key_facts": true,
  "quotes_and_document": true,
  "predicted_page": true
}
```

## R8

Question request:

```json
{
  "question": "How many days can I work from home?"
}
```

Predicted expectation:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Up to 2 days per week with line manager approval.",
  "Page": "1"
}
```

Actual response and latency:

```json
{
  "status_code": 200,
  "seconds": 2.844,
  "body": {
    "status": "ANSWERED",
    "answer": "Employees may work remotely up to 2 days per week with prior approval from their line manager. [1]",
    "citations": [
      {
        "document_id": "7b81582e25e944a1ac99f518a5b2ef8d",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 1,
        "chunk_id": "c9bc3fcb856148129724215cc5a6af3b_0",
        "quote": "Employees may work remotely up to 2 days per week with prior approval from their line\nmanager."
      }
    ]
  }
}
```

Checks:

```json
{
  "http_200": true,
  "predicted_status": true,
  "key_facts": true,
  "quotes_and_document": true,
  "predicted_page": true
}
```

## R18

Question request:

```json
{
  "question": "Can employees take unpaid leave?"
}
```

Predicted expectation:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Up to 15 days with director approval.",
  "Page": "2"
}
```

Actual response and latency:

```json
{
  "status_code": 200,
  "seconds": 5.141,
  "body": {
    "status": "ANSWERED",
    "answer": "Unpaid leave: Up to 15 days of unpaid leave may be granted with director approval. [1]",
    "citations": [
      {
        "document_id": "7b81582e25e944a1ac99f518a5b2ef8d",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 2,
        "chunk_id": "c9bc3fcb856148129724215cc5a6af3b_1",
        "quote": "Unpaid leave: Up to 15 days of unpaid leave may be granted with director approval."
      }
    ]
  }
}
```

Checks:

```json
{
  "http_200": true,
  "predicted_status": true,
  "key_facts": true,
  "quotes_and_document": true,
  "predicted_page": true
}
```

## R12

Question request:

```json
{
  "question": "What is the sick leave policy and what is the stock option policy?"
}
```

Predicted expectation:

```json
{
  "Status": "PARTIAL",
  "Answer must contain": "Answers sick leave (10 days) and states that stock options are not covered.",
  "Page": "2"
}
```

Actual response and latency:

```json
{
  "status_code": 503,
  "seconds": 14.016,
  "body": {
    "error": {
      "code": "ANSWER_UNSUPPORTED",
      "message": "Answer evidence failed verification",
      "requestId": "e6d9483266134eb7bb77aec7ddd268c5"
    }
  }
}
```

Checks:

```json
{
  "http_200": false,
  "predicted_status": false,
  "key_facts": false,
  "quotes_and_document": true,
  "predicted_page": false
}
```

## R14

Question request:

```json
{
  "question": "How many days of paternity leave are offered?"
}
```

Predicted expectation:

```json
{
  "Status": "INSUFFICIENT_EVIDENCE",
  "Answer must contain": "Must not reuse the 26 weeks of maternity leave or invent a number.",
  "Page": "–"
}
```

Actual response and latency:

```json
{
  "status_code": 503,
  "seconds": 9.234,
  "body": {
    "error": {
      "code": "ANSWER_UNSUPPORTED",
      "message": "Answer claims failed support verification",
      "requestId": "aeb7b1491a5d4310b9dbfe3bf73ca3d6"
    }
  }
}
```

Checks:

```json
{
  "http_200": false,
  "predicted_status": false,
  "key_facts": true,
  "quotes_and_document": true
}
```

## R19

Question request:

```json
{
  "question": "What must I do with my laptop when I leave?"
}
```

Predicted expectation:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Return it on the last working day.",
  "Page": "3"
}
```

Actual response and latency:

```json
{
  "status_code": 200,
  "seconds": 2.625,
  "body": {
    "status": "ANSWERED",
    "answer": "You must return your laptop on the last working day. [1]",
    "citations": [
      {
        "document_id": "7b81582e25e944a1ac99f518a5b2ef8d",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 3,
        "chunk_id": "c9bc3fcb856148129724215cc5a6af3b_2",
        "quote": "Laptops remain company property and must be returned on the last working\nday."
      }
    ]
  }
}
```

Checks:

```json
{
  "http_200": true,
  "predicted_status": true,
  "key_facts": true,
  "quotes_and_document": true,
  "predicted_page": true
}
```

## R17

Question request:

```json
{
  "question": "Is the annual leave 30 days?"
}
```

Predicted expectation:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Corrects the premise: it is 24 days.",
  "Page": "2"
}
```

Actual response and latency:

```json
{
  "status_code": 200,
  "seconds": 2.812,
  "body": {
    "status": "ANSWERED",
    "answer": "Annual leave is 24 days per calendar year. [1]",
    "citations": [
      {
        "document_id": "7b81582e25e944a1ac99f518a5b2ef8d",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 2,
        "chunk_id": "c9bc3fcb856148129724215cc5a6af3b_1",
        "quote": "Annual leave: Full-time employees receive 24 days of paid annual leave per calendar\nyear."
      }
    ]
  }
}
```

Checks:

```json
{
  "http_200": true,
  "predicted_status": true,
  "key_facts": true,
  "quotes_and_document": true,
  "predicted_page": true
}
```

## Reproduce

```powershell
.venv\Scripts\python.exe -m scripts.policy_condition_regression
```
