django-zen-queries
====================

[![Build Status](https://travis-ci.com/dabapps/django-zen-queries.svg?branch=master)](https://travis-ci.com/dabapps/django-zen-queries)
[![pypi release](https://img.shields.io/pypi/v/django-zen-queries.svg)](https://pypi.python.org/pypi/django-zen-queries)


Gives you control over which parts of your code are allowed to run queries, and which aren't.

Tested against Django 1.8, 1.11, 2.0, 2.1 and 2.2 on Python 2.7, 3.5, 3.6 and 3.7

### Motivation

> Explicit is better than implicit

(The [Zen Of Python](https://www.python.org/dev/peps/pep-0020/))

The greatest strength of Django's ORM is also its greatest weakness. By freeing developers from having to think about when database queries are run, the ORM encourages developers to _not think about when database queries are run!_ This often has great benefits for quick development turnaround, but can have major performance implications in anything other than trivially simple systems.

Django's ORM makes queries _implicit_. The Zen of Python tells us that **explicit is better than implicit**, so let's be explicit about which parts of our code are allowed to run queries, and which aren't.

Check out [this blog post](https://www.dabapps.com/blog/performance-issues-caused-by-django-implicit-database-queries/) for more background.

### Example

Imagine a pizza restaurant website with the following models:

```python
class Topping(models.Model):
    name = models.CharField(max_length=100)


class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping)
```

And here's the menu view:

```python
def menu(request):
    pizzas = Pizza.objects.all()
    context = {'pizzas': pizzas}
    return render(request, 'pizzas/menu.html', context)
```

Finally, the template:

```
<h1>Pizza Menu</h1>

<ul>
{% for pizza in pizzas %}
  <li>{{ pizza.name }}</li>
{% endfor %}
</ul>
```

How many queries are run here? Well, the answer is easy to see: it's just one! The query emitted by `Pizza.objects.all()` is all you need to get the information to show on the menu.

Now: imagine the client asks for each pizza on the menu to include a count of how many toppings are on the pizza. Easy! Just change the template:

```
<h1>Pizza Menu</h1>

<ul>
{% for pizza in pizzas %}
  <li>{{ pizza.name }} ({{ pizza.toppings.count }})</li>
{% endfor %}
</ul>
```

But how many queries are run now? Well, this is the classic _n queries problem_. We now have one query to get all our pizzas, and then another query _per pizza_ to get the toppings count. The more pizzas we have, the slower the app gets. **And we probably won't discover this until the website is in production**.

If you were reading a Django performance tutorial, the next step would be to tell you how to fix this problem (`.annotate` and `Count` etc). But that's not the point. The example above is just an illustration of how code in different parts of the codebase, at different levels of abstraction, even possibly (in larger projects) the responsibility of different developers, can interact to result in poor performance. Object-oriented design encourages black-box implementation hiding, but hiding the points at which queries are executed is the _worst_ thing you can do if your aim is to build high-performance web applications. So how do we fix this without breaking all our abstractions?

There are two tricks here:

1. Prevent developers from accidentally running queries without realising.
2. Encourage code design that separates _fetching data_ from _rendering data_.

This package provides three very simple things:

1. A context manager to allow developers to be explicit about where queries are run.
2. A utility to make querysets less lazy.
3. Some tools to make it easy to use the context manager with Django templates and Django REST framework serializers.

To be absolutely clear: this package does _not_ give you any tools to actually improve your query patterns. It just tells you when you need to do it!

### Instructions

To demonstrate how to use `django-zen-queries`, let's go back to our example. We want to make it impossible for changes to a template to trigger queries. So, we change our view as follows:

```python
def menu(request):
    pizzas = Pizza.objects.all()
    context = {'pizzas': pizzas}
    with queries_disabled():
        return render(request, 'pizzas/menu.html', context)
```

The `queries_disabled` context manager here does one very simple thing: it stops any code inside it from running database queries. At all. If they try to run a query, the application will raise a `QueriesDisabledError` exception and blow up.

That's _almost_ enough to give us what we need, but not quite. The code above will _always_ raise a `QueriesDisabledError`, because the queryset (`Pizza.objects.all()`) is _lazy_. The database query doesn't actually get run until the queryset is iterated - which happens in the template! So, `django-zen-queries` provides a tiny helper function, `fetch`, which forces evaluation of a queryset:

```python
def menu(request):
    pizzas = Pizza.objects.all()
    context = {'pizzas': fetch(pizzas)}
    with queries_disabled():
        return render(request, 'pizzas/menu.html', context)
```

Now we have exactly what we need: when a developer comes along and adds `{{ pizza.toppings.count }}` in the template, **it just _won't work_**. They will be forced to figure out how to use `annotate` and `Count` in order to get the data they need _up front_, rather than sometime in the future when customers are complaining that the website is getting slower and slower!

#### Decorator

You can also use `queries_disabled` as a decorator to prohibit database interactions for a whole function or method:
```
@queries_disabled()
def validate_xyz(pizzas):
    ...
```

This also works with Django's [`method_decorator`](https://docs.djangoproject.com/en/3.0/topics/class-based-views/intro/#decorating-the-class) utility.

### Extra tools

As well as the context managers, the package provides some tools to make it easier to use in common situations:

#### Render shortcut

If you're using the Django `render` shortcut (as in the example above), to avoid having to add the context manager to every view, you can change your import `from django.shortcuts import render` to `from zen_queries import render`. All the views in that file will automatically be disallowed from running queries during template rendering.

#### TemplateResponse subclass

`TemplateResponse` (and `SimpleTemplateResponse`) objects are lazy, meaning that template rendering happens on the way "out" of the Django stack. `zen_queries.TemplateResponse` and `zen_queries.SimpleTemplateResponse` are subclasses of these with `queries_disabled` applied to the `render` method.

#### Django REST framework Serializer and View mixins

Django REST framework serializers are another major source of unexpected queries. Adding a field to a serializer (perhaps deep within a tree of nested serializers) can very easily cause your application to suddenly start emitting hundreds of queries. `zen_queries.rest_framework.QueriesDisabledSerializerMixin` can be added to any serializer to wrap `queries_disabled` around the `.data` property, meaning that the serialization phase is not allowed to execute any queries.

You can add this mixin to an existing serializer *instance* with `zen_queries.rest_framework.disable_serializer_queries` like this: `serializer = disable_serializer_queries(serializer)`.

If you're using REST framework generic views, you can also add a view mixin, `zen_queries.rest_framework.QueriesDisabledViewMixin`, which overrides `get_serializer` to mix the `QueriesDisabledSerializerMixin` into your existing serializer. This is useful because you may want to use the same serializer class between multiple views but only disable queries in some contexts, such as in a list view.  Remember that Python MRO is left-right, so the mixin must come before (to the left of) any base classes that implement `get_serializer`. The view mixin only disables queries on `GET` requests, so can safely be used with `ListCreateAPIView` and similar.

#### Escape hatch

If you absolutely definitely can't avoid running a query in a part of your codebase that's being executed under a `queries_disabled` block, there is another context manager called `queries_dangerously_enabled` which allows you to temporarily re-enable database queries.

### Permissions gotcha

Accessing permissions in your templates (via the `{{ perms }}` template variable) can be a source of queries at template-render time. Fortunately, Django's permission checks are [cached by the `ModelBackend`](https://docs.djangoproject.com/en/2.2/topics/auth/default/#permission-caching), which can be pre-populated by calling `request.user.get_all_permissions()` in the view, before rendering the template.

### How does it work?

Probably best not to ask.

### Installation

Install from PyPI

    pip install django-zen-queries

## Code of conduct

For guidelines regarding the code of conduct when contributing to this repository please review [https://www.dabapps.com/open-source/code-of-conduct/](https://www.dabapps.com/open-source/code-of-conduct/)
