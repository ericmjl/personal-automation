# Minimal devcontainer.
FROM condaforge/mambaforge

COPY environment.yml /environment.yml
RUN mamba env update -f /environment.yml -n base && rm /environment.yml

# Add additional utilities needed at the operating system-level.
