# Policy 4 Document Regression

Workflow: fresh `POST /documents` followed by `POST /documents/{id}/questions`.

Seven targeted cases from the AI-assisted self-test pack with predicted expectations; this is not a new 76-case pass count.
R14 checks topic absence before generation. R12 sends only the supported question part to the generator, verifies its claims, and returns PARTIAL with the uncovered part named.
The lexical guard checks retrieved evidence and recognized content modifiers; it is conservative and can miss synonyms. It does not prove absence from the entire document.

## Fresh Upload

```json
{
  "status_code": 201,
  "seconds": 1.329,
  "body": {
    "document": {
      "id": "684dd6a373ab41978b065c4844475127",
      "filename": "Employee_Handbook_Test.pdf",
      "state": "READY",
      "pages": 3,
      "chunks": 3,
      "created": 1791494885.281679,
      "error": null
    },
    "status": "READY"
  }
}
```

## R2

Input:

```json
{
  "question": "Can I carry over unused leave?"
}
```

Predicted expectations:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Up to 5 days, to be used by 31 March.",
  "Page": "2"
}
```

Actual response and elapsed seconds:

```json
{
  "status_code": 200,
  "seconds": 3.687,
  "body": {
    "status": "ANSWERED",
    "answer": "Carry-over: Up to 5 unused days may be carried into the next year and must be used by 31 March. [1]",
    "citations": [
      {
        "document_id": "684dd6a373ab41978b065c4844475127",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 2,
        "chunk_id": "d31f5bc01cac42fb8a62db29de24f73a_1",
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

Input:

```json
{
  "question": "How many days can I work from home?"
}
```

Predicted expectations:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Up to 2 days per week with line manager approval.",
  "Page": "1"
}
```

Actual response and elapsed seconds:

```json
{
  "status_code": 200,
  "seconds": 2.937,
  "body": {
    "status": "ANSWERED",
    "answer": "Employees may work remotely up to 2 days per week with prior approval from their line manager. [1]",
    "citations": [
      {
        "document_id": "684dd6a373ab41978b065c4844475127",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 1,
        "chunk_id": "d31f5bc01cac42fb8a62db29de24f73a_0",
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

Input:

```json
{
  "question": "Can employees take unpaid leave?"
}
```

Predicted expectations:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Up to 15 days with director approval.",
  "Page": "2"
}
```

Actual response and elapsed seconds:

```json
{
  "status_code": 200,
  "seconds": 2.875,
  "body": {
    "status": "ANSWERED",
    "answer": "Up to 15 days of unpaid leave may be granted with director approval. [1]",
    "citations": [
      {
        "document_id": "684dd6a373ab41978b065c4844475127",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 2,
        "chunk_id": "d31f5bc01cac42fb8a62db29de24f73a_1",
        "quote": "Up to 15 days of unpaid leave may be granted with director approval."
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

Input:

```json
{
  "question": "What is the sick leave policy and what is the stock option policy?"
}
```

Predicted expectations:

```json
{
  "Status": "PARTIAL",
  "Answer must contain": "Answers sick leave (10 days) and states that stock options are not covered.",
  "Page": "2"
}
```

Actual response and elapsed seconds:

```json
{
  "status_code": 200,
  "seconds": 3.281,
  "body": {
    "status": "PARTIAL",
    "answer": "Sick leave: Employees receive 10 days of paid sick leave per year. A medical certificate is required after 3 consecutive days of absence. [1]\nThe document does not provide sufficient evidence for every part of this question. Uncovered question: what is the stock option policy?",
    "citations": [
      {
        "document_id": "684dd6a373ab41978b065c4844475127",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 2,
        "chunk_id": "d31f5bc01cac42fb8a62db29de24f73a_1",
        "quote": "Sick leave: Employees receive 10 days of paid sick leave per year. A medical certificate is\nrequired after 3 consecutive days of absence."
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

## R14

Input:

```json
{
  "question": "How many days of paternity leave are offered?"
}
```

Predicted expectations:

```json
{
  "Status": "INSUFFICIENT_EVIDENCE",
  "Answer must contain": "Must not reuse the 26 weeks of maternity leave or invent a number.",
  "Page": "–"
}
```

Actual response and elapsed seconds:

```json
{
  "status_code": 200,
  "seconds": 0.062,
  "body": {
    "status": "INSUFFICIENT_EVIDENCE",
    "answer": "The uploaded document does not provide sufficient evidence to answer this question.",
    "citations": []
  }
}
```

Checks:

```json
{
  "http_200": true,
  "predicted_status": true,
  "key_facts": true,
  "quotes_and_document": true
}
```

## R19

Input:

```json
{
  "question": "What must I do with my laptop when I leave?"
}
```

Predicted expectations:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Return it on the last working day.",
  "Page": "3"
}
```

Actual response and elapsed seconds:

```json
{
  "status_code": 200,
  "seconds": 2.891,
  "body": {
    "status": "ANSWERED",
    "answer": "Return your laptop on the last working day. [1]",
    "citations": [
      {
        "document_id": "684dd6a373ab41978b065c4844475127",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 3,
        "chunk_id": "d31f5bc01cac42fb8a62db29de24f73a_2",
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

Input:

```json
{
  "question": "Is the annual leave 30 days?"
}
```

Predicted expectations:

```json
{
  "Status": "ANSWERED",
  "Answer must contain": "Corrects the premise: it is 24 days.",
  "Page": "2"
}
```

Actual response and elapsed seconds:

```json
{
  "status_code": 200,
  "seconds": 3.047,
  "body": {
    "status": "ANSWERED",
    "answer": "Annual leave is 24 days per calendar year. [1]",
    "citations": [
      {
        "document_id": "684dd6a373ab41978b065c4844475127",
        "filename": "Employee_Handbook_Test.pdf",
        "page": 2,
        "chunk_id": "d31f5bc01cac42fb8a62db29de24f73a_1",
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
