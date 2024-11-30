# Use the official Python image
FROM python:3.13.0

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
# COPY requirements.txt .

# Install the requirements
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask
RUN pip install pymysql
RUN pip install pandas
RUN pip install flasgger
# Copy the current directory contents into the container
COPY . .

# Command to run the FastAPI server
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
