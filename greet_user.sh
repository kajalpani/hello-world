#!/bin/bash
#This is just a demo file
if [ -z $1 ]; then
	echo "Please pass your name as argument to script"
	exit 1 
fi
echo "Hey how are you doing?" $1
