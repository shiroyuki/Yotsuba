/*
 *  yotsuba.h
 *  Tamaki
 *
 *  Created by Juti Noppornpitak on 10-01-09.
 *  Copyright 2010 Shiroyuki Studio. All rights reserved.
 *
 */

void core_raise(char * exceptionMessage);
long int file_size(FILE * filePointer);
char * file_read(char * filePath, int doReadBinary);