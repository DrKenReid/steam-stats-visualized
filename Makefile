.PHONY: run test install

install:
	pip install -r requirements.txt

run:
	streamlit run app.py

test:
	pytest tests/ -v
