# Use the official Python image as the base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt first (to leverage Docker's layer caching)
COPY requirements.txt .

# Install Firefox to get page sources
RUN apt-get update && apt-get install -y firefox-esr \
    && apt-get clean \
    && pip install --no-cache-dir -r requirements.txt

# Copy everything except the "articles" folder
COPY . /app

# Expose the desired port
EXPOSE 1235

# Define the command to run the application
CMD ["hypercorn", "-w", "4", "-b", "0.0.0.0:1235", "main.py"]


# To build and run
# 1) docker build -t read-up .
# 2) docker run --env-file .\.env -p 1235:1235 read-up