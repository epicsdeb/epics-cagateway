/*************************************************************************\
* Copyright (c) 2002 The University of Chicago, as Operator of Argonne
* National Laboratory.
* Copyright (c) 2002 Berliner Speicherring-Gesellschaft fuer Synchrotron-
* Strahlung mbH (BESSY).
* Copyright (c) 2002 The Regents of the University of California, as
* Operator of Los Alamos National Laboratory.
* This file is distributed subject to a Software License Agreement found
* in the file LICENSE that is included with this distribution.
\*************************************************************************/
/* Author: Jim Kowalkowski
 * Date: 7/96 */

#ifndef tsDLHashList_H
#define tsDLHashList_H

extern "C" {
#include "gpHash.h"
}

#include "tsDLList.h"

template <class T>
class tsHash
{
private:
	gphPvt * hash_table;
	// friend class tsDLHashIter<T>;

public:
    tsHash(void)
	{
		hash_table=0;
		gphInitPvt(&hash_table,2048); // 2048 is a guess
	}

	~tsHash(void)
	{
		gphFreeMem(hash_table);
	}

	int add(const char* key, T& item)
	{
		GPHENTRY* entry;
		int rc;

		entry=gphAdd(hash_table,(char*)key,hash_table);

		if(entry==0)
			rc=-1;
		else
		{
			entry->userPvt=(void*)&item;
			rc=0;
		}
		return rc;
	}

	int remove(const char* key,T*& item)
	{
		int rc;

		if(find(key,item)<0)
			rc=-1;
		else
		{
			gphDelete(hash_table,(char*)key,hash_table);
			rc=0;
		}
		return rc;
	}

	int find(const char* key, T*& item)
	{
		GPHENTRY* entry;
		int rc;

		entry=gphFind(hash_table,(char*)key,hash_table);

		if(entry==0)
			rc=-1;
		else
		{
			item=(T*)entry->userPvt;
			rc=0;
		}
		return rc;
	}
};

template <class T>
class tsDLHashList : public tsDLList<T>
{
private:
	tsHash<T> h;
	// friend class tsDLHashIter<T>;

public:
	tsDLHashList(void) { }
	~tsDLHashList(void) { }

	int add(const char* key, T& item)
	{
		int rc;
		rc=h.add(key,item);
		tsDLList<T>::add(item);
		return rc;
	}

	int find(const char* key, T*& item)
	{
		int rc=0;
		if(h.find(key,item)!=0)
			rc=-1;
		return rc;
	}

	int remove(const char* key,T*& item)
	{
		int rc=0;
		if(h.find(key,item)==0)
		{
			h.remove(key,item);
			tsDLList<T>::remove(*item);
		}
		else
			rc=-1;
		return rc;
	}
};

template <class T>
class tsDLHashNode : public tsDLNode<T>
{
public:
#if 0
  // These are now private
    T* getNext(void) { return tsDLNode<T>::getNext(); }
    T* getPrev(void) { return tsDLNode<T>::getPrev(); }
#endif
};

#endif
