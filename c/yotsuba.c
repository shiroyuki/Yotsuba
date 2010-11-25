/*
 *  yotsuba.c
 *  Tamaki
 *
 *  Created by Juti Noppornpitak on 10-01-09.
 *  Copyright 2010 Shiroyuki Studio. All rights reserved.
 *
 */

#include <stdio.h>
#include "yotsuba.h"

void core_raise(char * exceptionMessage) {
	fputs(exceptionMessage, stderr);
	exit(1);
}

long int file_size(FILE * filePointer) {
	long int fileSize;
	
	fseek (filePointer , 0 , SEEK_END);
	fileSize = ftell (filePointer);
	rewind (filePointer);
	
	return fileSize;
}

char * file_read(char * filePath, int doReadBinary) {
	char *fileContent;
	long int fileSize;
	size_t bufferSize;
	FILE *fp;
	
	fp = fopen(filePath, doReadBinary?"rb":"r");
	
	if (!fp) {
		core_raise("Yotsuba: Cannot read the file");
	}
	
	// obtain file size:
	fileSize = file_size(fp);
	
	fileContent = (char *) malloc(sizeof(char) * fileSize);
	if (!fileContent) {
		core_raise("Yotsuba: Cannot allocate memory for reading.");
	}
	
	// copy the file content into the buffer:
	bufferSize = fread (fileContent, 1, fileSize, fp);
	if (bufferSize != fileSize) {
		core_raise("Yotsuba: Reading incomplete.");
	}
	
	fclose(fp);
	
	return fileContent;
}