# Use the official Python image as the base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt first (to leverage Docker's layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything except the "articles" folder
COPY . /app
RUN rm -rf /app/articles

# Expose the desired port
EXPOSE 1235

# Define the command to run the application
CMD ["python", "main.py"]


# To build and run
# 1) docker build -t read-up .
# 2) docker run --env-file .\.env -p 1235:1235 read-up