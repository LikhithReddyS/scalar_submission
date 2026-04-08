# Read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# you will also find guides on how best to write your Dockerfile

FROM python:3.10-slim

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Set home to the user's home directory and path
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the requirements file into the container
COPY --chown=user:user ../requirements.txt $HOME/app/requirements.txt

# Switch to the "user" user so installations happen in their ~/.local
USER user

# Install dependencies with --user flag to avoid permission issues
RUN pip install --user --no-cache-dir --upgrade -r $HOME/app/requirements.txt

# Copy the rest of the application code into the container
COPY --chown=user:user .. $HOME/app

# Command to run the application
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
