# Docker Assignment

Jakub Ryłow

Environment: GitHub Codespaces, `docker:default` builder.

```
$ docker --version
Docker version 29.7.2-2, build a7dcaa6fdb6ed04aacbfdc76357fdae01605609e
```

Build logs below are abridged in the middle (`...`) as in the example in the
assignment; the first and last lines of each build are unchanged.

## Task 1.1 — Change the Python version

The `Dockerfile` from class was edited to use `python:3.9-slim` instead of
`python:3.11-slim`, then rebuilt and run.

```
$ cat > hello.py << 'EOF'
import sys
print(f"Hello from Python {sys.version_info.major}.{sys.version_info.minor} inside a container!")
EOF
$ cat > Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
COPY hello.py .
CMD ["python", "hello.py"]
EOF
$ docker build -t hello-docker .
[+] Building 5.4s (9/9) FINISHED                                        docker:default
 => [internal] load build definition from Dockerfile                              0.0s
 => => transferring dockerfile: 114B                                              0.0s
 => [internal] load metadata for docker.io/library/python:3.9-slim                1.1s
 => [auth] library/python:pull token for registry-1.docker.io                     0.0s
 => [internal] load .dockerignore                                                 0.0s
 => [1/3] FROM docker.io/library/python:3.9-slim@sha256:2d97f6910b16bd338d3060f2   2.4s
 => => sha256:38513bd7256313495cdd83b3b0915a633cfa475dc2a07072ab2c8d191020ca5d 29.78MB  0.9s
 => => extracting sha256:38513bd7256313495cdd83b3b0915a633cfa475dc2a07072ab2c8d1  0.9s
 ...
 => [2/3] WORKDIR /app                                                            1.6s
 => [3/3] COPY hello.py .                                                         0.0s
 => exporting to image                                                            0.2s
 => => exporting manifest sha256:251233a25c63d9edee2a5e1651e4bbcdb20f72037f8a439  0.0s
 => => naming to docker.io/library/hello-docker:latest                            0.0s
 => => unpacking to docker.io/library/hello-docker:latest                         0.0s
$ docker run --rm hello-docker
Hello from Python 3.9 inside a container!
```

The host machine runs a different Python version; the container reports 3.9
because the base image fixes it.

## Task 1.2 — Break and fix the Dockerfile

### The failure

`hello.py` was replaced with the version that imports `pandas`, and the image
rebuilt without any change to the `Dockerfile`.

```
$ cat > hello.py << 'EOF'
import sys, pandas
print(f"Python {sys.version_info.major}.{sys.version_info.minor}, pandas {pandas.__version__}")
EOF
$ docker build -t hello-docker .
[+] Building 0.6s (8/8) FINISHED                                        docker:default
 => [internal] load build definition from Dockerfile                              0.0s
 => => transferring dockerfile: 114B                                              0.0s
 => [internal] load metadata for docker.io/library/python:3.9-slim                0.3s
 => [1/3] FROM docker.io/library/python:3.9-slim@sha256:2d97f6910b16bd338d3060f2   0.0s
 => CACHED [2/3] WORKDIR /app                                                     0.0s
 => [3/3] COPY hello.py .                                                         0.0s
 ...
 => => naming to docker.io/library/hello-docker:latest                            0.0s
$ docker run --rm hello-docker
Traceback (most recent call last):
  File "/app/hello.py", line 1, in <module>
    import sys, pandas
ModuleNotFoundError: No module named 'pandas'
```

Note that the *build* succeeded. Nothing in the `Dockerfile` is wrong as an
instruction to Docker; the image simply does not contain pandas, and that only
surfaces when the container runs. `python:3.9-slim` is deliberately minimal and
ships nothing beyond the standard library.

### The fix

One line added, with the version pinned:

```
$ cat > Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
RUN pip install pandas==2.2.2
COPY hello.py .
CMD ["python", "hello.py"]
EOF
$ docker build -t hello-docker .
[+] Building 22.2s (9/9) FINISHED                                       docker:default
 => [internal] load build definition from Dockerfile                              0.0s
 => => transferring dockerfile: 144B                                              0.0s
 => [internal] load metadata for docker.io/library/python:3.9-slim                0.2s
 => [1/4] FROM docker.io/library/python:3.9-slim@sha256:2d97f6910b16bd338d3060f2   0.0s
 => CACHED [2/4] WORKDIR /app                                                     0.0s
 => [3/4] RUN pip install pandas==2.2.2                                          12.4s
 => [4/4] COPY hello.py .                                                         0.1s
 => exporting to image                                                            9.5s
 ...
 => => naming to docker.io/library/hello-docker:latest                            0.0s
 => => unpacking to docker.io/library/hello-docker:latest                         1.5s
$ docker run --rm hello-docker
Python 3.9, pandas 2.2.2
```

`RUN pip install` was placed *before* `COPY hello.py .` on purpose. Docker
caches layers in order, so editing the script afterwards re-runs only the copy
and not the twelve-second install — visible in the run above, where `WORKDIR`
came back as `CACHED`.

### Final Dockerfile

```
FROM python:3.9-slim
WORKDIR /app
RUN pip install pandas==2.2.2
COPY hello.py .
CMD ["python", "hello.py"]
```

## Question 2.1 — Why pin?

With `RUN pip install pandas` the `Dockerfile` stops being a full description
of the environment: it says "whatever pandas pip considers newest at the moment
someone happens to build this", which is a different answer on every rebuild.
Today it yields 2.2.2; a rebuild next year could yield 3.x, and a rebuild on a
machine with an older Python could resolve to something much older still. The
concrete failure modes split in two, and the quieter one is worse. A removed
function or renamed argument breaks the build loudly, which at least tells you
something changed; but a change to a default — how `groupby` handles missing
keys, which dtype an empty column gets, how a numeric string is parsed — leaves
the code running and silently returns different numbers. The timing is the
cruel part: nothing fails while you are working, because your image is already
built. It fails when you rebuild, which is precisely when you can least afford
it — a reviewer checking your results, a new laptop after the old one died, or
a co-author trying to confirm a figure months after publication.

## Question 2.2 — Recipe or cake?

Sending the `Dockerfile` and `hello.py` is better, and the reason is
inspectability rather than convenience. A built image is an opaque artifact: a
colleague can run it and observe what it produces, but cannot see what it
claims about its own environment, cannot diff this version against the previous
one, and cannot review whether the environment is appropriate for the analysis.
The recipe can be read, criticised, version-controlled, and reused for a
different Python version or a different architecture — a reviewer can check
that pandas is pinned at all, which is exactly the question 2.1 is about, and
that check is impossible from the outside of an image. There is also a
practical point about permanence: a tag on Docker Hub can be deleted, or
overwritten so that the same name later refers to a different image, whereas a
text file in a repository has a commit history.

The honest qualification is that the recipe alone does not guarantee an
identical environment. `pip install pandas==2.2.2` still resolves numpy and the
rest at build time, and the base image tag can move. The stronger answer is the
recipe plus a lockfile and a digest-pinned base (`FROM python:3.9-slim@sha256:...`),
which keeps the readability of the recipe and most of the determinism of the
cake.
