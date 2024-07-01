FROM python:3.12-slim

ARG USER_ID
ARG USER_NAME

ENV HOME=/home/${USER_NAME} \
    VIRTUAL_ENV=/home/${USER_NAME}/venv
ENV \
  PYTHONUNBUFFERED=1 \
  DEBIAN_FRONTEND=noninteractive \
  TZ=America/Sao_Paulo \
  PATH="/usr/local/gcloud/google-cloud-sdk/bin:${HOME}/.local/bin:${VIRTUAL_ENV}/bin:${PATH}" \
  PYTHONPATH="/app:${PYTHONPATH}" \
  BUILD_POETRY_LOCK="${HOME}/poetry.lock.build"  

# Install some packages
RUN apt-get -qq update \
  && apt-get -qq -y install vim gcc curl git build-essential libb64-dev software-properties-common \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get -qq -y clean

# Install GCloud
RUN curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-426.0.0-linux-x86_64.tar.gz > /tmp/google-cloud-sdk.tar.gz
RUN mkdir -p /usr/local/gcloud \
    && tar -C /usr/local/gcloud -xf /tmp/google-cloud-sdk.tar.gz \
    && /usr/local/gcloud/google-cloud-sdk/install.sh --usage-reporting false --command-completion true --bash-completion true --path-update true --quiet

# Creating user
RUN addgroup --system --gid ${USER_ID} ${USER_NAME} \
    && useradd --system -m --no-log-init --home-dir ${HOME} --uid ${USER_ID} --gid ${USER_NAME} --groups ${USER_NAME} ${USER_NAME}

# Changing Owner of the folder
RUN chown -R ${USER_NAME}:${USER_NAME} ${HOME}

# Creating some folders
RUN mkdir -p /app && chown -R ${USER_NAME}:${USER_NAME} /app /tmp

# Installing Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
# Define USER as user_name.
USER ${USER_NAME}

# Copying everything we need to our project to /app folder
COPY pyproject.toml *.lock /app/

# Make /app folder our work directory
WORKDIR /app

# Install our dependencies
RUN python3 -m venv ${VIRTUAL_ENV} \
    && . ${VIRTUAL_ENV}/bin/activate \
    && pip install --upgrade pip setuptools \
    && poetry config virtualenvs.create false \
    && poetry install \
    && cp poetry.lock ${BUILD_POETRY_LOCK} \
    && rm -rf ${HOME}/.cache/*

# Switch back to the root user
#   Because we need root permission to run the scripts below
USER root

# Copy scripts
COPY ./docker/scripts/* /

# Make user owner and make scripts executable
RUN chown -R ${USER_NAME} /*.sh && chmod +x /*.sh

# Switch back to user again
USER ${USER_NAME}

# Copy our application code
COPY . /app/

# Run the command
CMD ["/startup-script.sh"]



