import lmstudio as lms

# подключаемся к LM Studio (по умолчанию localhost:1234)
model = lms.llm()

# проверим, отвечает ли модель
response = model.complete("Привет! Расскажи короткий факт о космосе.")
print(response)
