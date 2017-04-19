<!--
Copyright 2015 F5 Networks Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

#Contributing Guide for F5-CCCL

As of this day, 4/19/2017, we are not accepting any community contribution for
an unknown period of time.  Such contributions that are submitted will be
reviewed by F5 personnel; however, there is no promise nor accepted obligation
to accept such code, additions to code, refactorings, thoughts, or ideas.

We greatly appreciate such enthusiasm; however, the F5 CCCL team would like
to first get a major release out before considering contributions provided
from outside of F5.

##Branching Strategy

This repo will largely follow [semantic versioning](http://semver.org/) and will
also use [release branching as outlined in gitlab flow](https://docs.gitlab.com/ee/workflow/gitlab_flow.html#release-branches-with-gitlab-flow).
This includes the [11 rules of gitlab flow](https://about.gitlab.com/2016/07/27/the-11-rules-of-gitlab-flow/)

To support bug fixes on released images, while also allowing new features,
including breaking changes, we maintain a series of stable branches.

Changes that go into one of the stable branches need to honor the semantic
versioning requirements. e.g. a new feature must result in a minor version bump
in the next release. A breaking change must result in a major version bump.

##Pull Request (PR) Best Practices

Any new commits into the master branch should come in as a pull request whether
it being from a long-standing feature branch or in the form of a very small bug
fix.

Commits performed on a user’s forking branch that are then submitted for peer
review in the form of a pull request should be made with multiple commits when
appropriate.  This may apply when there are multiple changes that impact
multiple files, but requires a multi-step process logically; however, when
removing a commit, it should not be a make or break scenario.  The commit should
be standalone such that the product will work under normal circumstances of
runtime with or without the commit.  This breaks out the work logically into the
steps required to achieve the goal into a readable fashion; however, these
commits should be made to appear in order to clean up the appearance of the
change for readability purposes.

This means that any staged commits performed that are not standalone should be
squashed into one commit and ordered appropriately using commands like rebase -i
to edit the staged commits.  in the case where a pull request reaches a scenario
where it is necessary to resolve conflicts with master, then changes should be
performed to the earlier commit to make the earlier commits stable.  Then the
new commit that merges the forked scenario should be its own commit.

This should help with later cherry picking that is acknowledged will happen down
the road by making each change more readable.

Following this best practice, converged diff -u example might be:
```python
0class Foo(object):
1     check_re = re.compile(check_expr)
2     Group = namedtuple(‘Group’, ‘alpha, beta, zeta’)
3     __nonzero = False
4
5     def __init__(self, str_in):
6          match = self.check_re.search(str_in)
7          if match:
8               self.match = self.Group(match.groups())
9               self.__nonzero = True
```
Here, we have the originally introduced code. This has the error of not coming
up as False result for foo in:

for line in content:

```python
foo = Foo()
if foo:
print("{}: {} - {}".format(foo.alpha, foo.beta,
foo.zeta)
This is the bug that the following pull requests will attempt to fix.
```

What Incorrectly Marked-up Code Might Look Like:

```python
 1+Groups = namedtuple(‘Group’, ‘alpha, beta, zeta’)
 2+
 3+
 4 class Foo(object):
 5+    __created = False
 6     check_re = re.compile(check_expr)
 7-    Group = namedtuple(‘Group’, ‘alpha, beta, zeta’)
 8-    __nonzero = False
 9
10     def __init__(self, str_in):
11          match = self.check_re.search(str_in)
12          if match:
13+              self.__created = True
14-              self.match = self.Group(match.groups())
15+              self.match = Group(match.groups())
16-              self.__nonzero = True
17
18+    def __nonzero__(self):
19+        return self.__created
```

Here, line 12 is showing up as an edit prior to the omission from the original
code at line 15. This disagrees with the typical flow of code given in
`diff -u` (or git `diff --no-prefix`). As such, this looks there was more things
changed than was actually being performed content-wise.

For logging and tallying this represents 8 amends and 4 redactions and a total
of 19 lines

Correctly Marked-up Code Commit 1:

```python
 0 class Foo(object):
 1      check_re = re.compile(check_expr)
 2      Group = namedtuple(‘Group’, ‘alpha, beta, zeta’)
 3      __nonzero = False
 4
 5      def __init__(self, str_in):
 6           match = self.check_re.search(str_in)
 7           if match:
 8                self.match = self.Group(match.groups())
 9                self.__nonzero = True
10
11+     def __nonzero__(self):
12+          return self.__nonzero 
```

Here, we can see that the actual fix is nothing more than 2 lines when made
appropriately and elegantly as a single commit. This differentiates other steps
and tasks that are required to be performed and justifies the commit author's
work.

A commit message might be:

> Issue #\<bug number\>
>
> Problem:
> That the runtime conditional of Foo() object does not evaluate properly under
> an if, or similar, conditional
>
> Analysis:
> Created Foo method, __nonzero__, that addresses runtime conditional not
> behaving as expected
> Tests:
> \<explicit unit test that covers this change and any new functional tests
> written\> 

Correctly Marked-up Code Commit 2:

```python
 0+Groups = namedtuple(‘Group’, ‘alpha, beta, zeta’)
 1+
 2+
 3 class Foo(object):
 4     check_re = re.compile(check_expr)
 5-    Group = namedtuple(‘Group’, ‘alpha, beta, zeta’)
 6-     __nonzero = False
 7+     __created = False
8
 9      def __init__(self, str_in):
10           match = self.check_re.search(str_in)
11           if match:
12-               self.match = self.Group(match.groups())
13+               self.match = Group(match.groups())
14-               self.__nonzero = True
15+               self.__created = True
16
17      def __nonzero__(self):
18-          return self.__nonzero
19+          return self.__created
```

Here, we can see distinctly what is being changed that is not completely bug
related as:

1. It's in its own commit
2. The lines that are being changed for simple renames and the like are right in sequence

This reorganizing of the code and renaming of different variables may be
performed for several different reasons. The key important thing here is that
the commit author specified exactly why this commit should be added to the
reviewer. It could be argued that since there are 2 essential changes here, that
they should be in their own separate commits. If there are tickets that these
changes individually address, then they definitely should be while citing
exactly which ones they address and why.

Correctly Marked-up Code Total Pull Request:

```python
 0+Groups = namedtuple(‘Group’, ‘alpha, beta, zeta’)
 1+
 2+
 3 class Foo(object):
 4     check_re = re.compile(check_expr)
 5-    Group = namedtuple(‘Group’, ‘alpha, beta, zeta’)
 6-     __nonzero = False
 7+     __created = False
 8
 9      def __init__(self, str_in):
10           match = self.check_re.search(str_in)
11           if match:
12-               self.match = self.Group(match.groups())
13+               self.match = Group(match.groups())
14-               self.__nonzero = True
15+               self.__created = True
16
17+     def __nonzero__(self):
18+          return self.__created
```

Here, we can see that the code, committed correctly, only has 8 appends and 4
removals and 18 lines total, which does match our Incorrect case; however, the
important aspect is that line 15 contains the line append that, subsequently, is
associated with line 14's removal. Rather than have this content split apart
making it look like more change than what is actually being incorporated.
Further, it is easier to read for the reviewer.

Lastly, with the pull request being in two separate commits addressing to
separate issues:

1. The bug assigned
 * Lines 17 and 18 in commit 1
2. Fixes to improve readability
 * Lines \[0-2, 5-7, 12-15\] in commit 2

This is then more easily consumed when performing and analyzing a git log after
the fact.

It could be argued that the above example is a situation of simple semantics and
could largely be ignored; however, it is an extreme example that helps to get
the information across.  Please keep changes close to where they were located in
the original code to endorse better readability.  It could also be argued that
the conflict of moving the rename variable around is mute because one could
simply add return hasattr(self, 'match') from within Foo.__nonzero__; however,
as it exists, this example provides the reasoning for why such changes should be
close to one another instead of spread out within scope (variable renames or
similar actions).

One of the key aspects here is that between commit 1 and commit 2 is that this
code would run as expected with or without one of these commits being present.

Lastly, by breaking things out in commits between what is logically being
changed, a better decision can be made on what gets cherry picked into a release
branch and what does not.  There are automated tools that can be used to detect
when a test fails for a specific commit, and the more precise our commits are,
the more useful such tools can be.

This is an example of a best practice, and within time limits, things like this
greatly improve overall readability.

##Conclusion

In most projects, code branching is generally a moving target, which leads to
confusion for both consumers and developers.  This results in unnecessary
frictions and frustrations for multiple parties; thus, to help prevent such
consequences, this document was written.  It is acknowledged that this document
represents nothing further than a set of guidelines; however, the actions of
those who do not follow such guidelines are subject to review by peers.  It is
not just the right of those who perform such reviews, but their duty to police
the enforcement of these guidelines.  This defines every contributor’s
responsibilities.

