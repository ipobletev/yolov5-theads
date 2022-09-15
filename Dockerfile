# Import python
FROM nvcr.io/nvidia/l4t-pytorch:r32.5.0-pth1.7-py3

# Folder to save data in other machine
WORKDIR /app

# Folder from host to image container (/app)
COPY . .

RUN export LC_ALL=C.UTF-8
RUN python3 -m pip install --upgrade pip
RUN pip3 install scikit-build
RUN pip3 install -r requirements.txt

# Change execution python folder
WORKDIR /app/src

CMD ["python3", "app.py"]