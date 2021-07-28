DOCKER_IMAGE_VERSION=1.01
DOCKER_IMAGE_NAME=churruscat/log-nmea
DOCKER_IMAGE_TAGNAME=$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_VERSION)

default: build
# First you need to prepare buildx => docker buildx create --name multi && docker buildx use multi

build:
	docker buildx build .  --platform=linux/arm64,linux/arm/v7 -t $(DOCKER_IMAGE_TAGNAME) -t $(DOCKER_IMAGE_NAME):latest --push 
#        docker buildx build .  --platform=linux/arm64,linux/arm/v7 --tag $(DOCKER_IMAGE_NAME):latest  
#	docker build -t $(DOCKER_IMAGE_TAGNAME) .
#	docker tag $(DOCKER_IMAGE_TAGNAME) $(DOCKER_IMAGE_NAME):latest

push:
# First use a "docker login" with username, password and email address
	docker push $(DOCKER_IMAGE_NAME)

test:
	docker run --rm $(DOCKER_IMAGE_TAGNAME) /bin/echo "Success."

rmi:
	docker rmi -f $(DOCKER_IMAGE_TAGNAME)

rebuild: rmi build

