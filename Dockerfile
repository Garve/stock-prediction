FROM continuumio/miniconda3

RUN conda update -n base -c defaults conda -y
RUN conda install -c conda-forge dash plotly fbprophet lxml -y
RUN pip install yfinance

EXPOSE 5000

COPY app.py app/
CMD python app/app.py
