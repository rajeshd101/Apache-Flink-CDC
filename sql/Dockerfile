# Use the official Flink image as the base
FROM flink:1.17.1-scala_2.12

# Install Python, Pip, and necessary build dependencies
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev && \
    ln -s /usr/bin/python3 /usr/bin/python

# Upgrade pip and install PyFlink
RUN pip3 install --upgrade pip
RUN pip3 install apache-flink==1.17.1

# Download the required JAR connectors into the Flink library folder
# This removes the need for 'wget' commands in your docker-compose file
RUN wget -P /opt/flink/lib https://repo1.maven.org/maven2/com/ververica/flink-sql-connector-mysql-cdc/2.4.1/flink-sql-connector-mysql-cdc-2.4.1.jar
RUN wget -P /opt/flink/lib https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-elasticsearch7/3.0.1-1.17/flink-sql-connector-elasticsearch7-3.0.1-1.17.jar