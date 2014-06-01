irkit
=====
[IRKit] command line tool for Mac OS X.

[IRKit]: http://getirkit.com

# Install

```
git clone https://github.com/kojiishi/irkit.git
cd irkit
sudo ln -s $PWD/irkit.py /usr/bin/irkit
```

# Recording

```
irkit save tv
```

# Playback

```
irkit tv
```

## Multiplier

Append `*` followed by a number to send multiple times.
```
irkit v-up*3
```
to send `v-up` 3 times.

# Scope

irkit has a concept of **scope**, which is similar to directories (and is actually implemented as directories.)

When recording, you always specify its name from the root scope, so the following two commands:
```
irkit save tv next
irkit save dvd next
```
will save signals to `/tv/next` and `/dvd/next` respectively.

When sending signals, irkit keeps track of the current scope.
```
irkit tv
irkit next
irkit dvd
irkit next
```
The first command changes the current scope to `/tv`.
Commands are searched first in the current scope,
and then its parent scopes,
so the second `next` command matches to `/tv/next`.

Since the third command `dvd` does not exist in the current `/tv` scope,
irkit searches for its parent (i.e., root) scope,
where it finds `dvd`.
The current scope is now changed to `/dvd`,
so the fourth `next` command matches to `/dvd/next`.
