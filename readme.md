# Domain Modeling

Notes

1. Not everything needs to be a method! You can define domain services as functions as well
2. These models define all of your business logic and rules

Takeaways

1. **These models should have ZERO dependencies**

# Repository Pattern

Notes

1. we didn't add a save method to our repository but that is very common
2. Common to have 1 repository that holds list/get/add for all aggregates + save for each type. Its just as common to have 1 repository for each aggregate for each type. Also common to have abstract repositories / interfaces for each aggregate. This allows you to add more custom methods / fields that you want on each implementation (more flexible). We will switch to this in chapter 5.

Takeaways

1. Different ORM packages around querying a database implement different APIs. In order to not depend on a specific ORM, we create an interface (a repository) around common db operations. We can then make our service layer depend on this interface and pass any defined repository you want
2. This points to a main concept of DDD. you create interfaces/repositories of infrastructure services your app layer will need and pass it in as a dependency so your app is very easily extensible and decoupled from infrastructure concerns

# Service Layer

Takeaways

1. These are your app services. They invoke your domain services and define an interface/entry points to your domain model.
2. Its important that these services depend on interfaces, rather than implementations. This promotes strong TDD and allows you to easily change infrastructure dependencies without having to rewrite any service

# TDD via Domain Model vs. Service Layer

Notes

1. When building a domain model, testing the model is very useful (in making sure it works). as your system matures, you tend to make less domain changes and a lot of infrastructure/scaling/refactoring changes.
2. Testing the service layer provides more business value, because it only works if domain model is working + infra concerns around it. as your system matures testing close to the end (integration tests) provide more value for every test written

Takeaways

1. Just freaking write tests, but testing too low breaks a lot of tests for every refactoring phase. Testing too far misses important details that are often overlooked / harder to write great test flows. We found focusing a lot on service layer to be the best, as it abstracts domain implementations but is close enough to still easily test all invariants/rules

# Unit of Work

Notes

1. There is significant overlap for each service in the service layer. Just about each function queries the database, runs some domain service, and commits the changes. We created an abstraction that automates this orchestration, called the unit of work pattern
2. One of the nice things about this pattern is that it abstracts away the aggregates/other db infra dependencies that would need to be passed to a service in the service layer. For instance, function A no longer needs ExampleRepositoryA, ExampleRepositoryB, and a db session corresponding to the type of repositories passed in (eg., SqlAlchemy). Rather, function A just needs the unit of work you created for a particular type of Repository (eg., SqlAlchemy UOW)
3. In this chapter we also stopped creating value objects and passing those in to the service layer, and just started passing in inputs we needed to create value object inside the service layer itself. The first way isn't a no no, but this change feels cleaner because now our transport layer is just validating payload input and calling app service.

Takeaways

1. Creating an N number of Repositories (for each aggregate) for each type M is pretty annoying (M x N), especially since your service layer will need to depend on N interfaces (of the same interface! which feels weird). To combat this, lots of teams create one repository for all entities for each type (M). This is fine and totally up to your team; however, UOW pattern abstracts away the (N) amount of repositories, so up to you!
2. We put our UOW inside the service layer folder, but you could very much argue that this is an adapter. it abstracts and works with a specific ORM implementation / repository implementation. However, functionally, UOW was made to make the service layer DRY

# Aggregates and Consistency Boundaries

Invariants:

1. An OrderLine can only be allocated to only one batch at a time
2. We cannot allocate to a batch if the available qty is less than OrderLine qty

Problem

1. Our domain model has invariants that must always be true when we are done with our invocation
   1a. this means we can bend the rules so long as the invariants are met by the end of whatever you are running
2. Our current allocate service is passing **ALL** of our batches in our entire system to the allocate domain function
   1a. this wont scale
3. We have not thought about how to maintain our invariants with concurrency (see below)
   2a. usually done with db locks / transaction isolation levels + versioning

Other Notes

1. Often few entities work together and are separated from the rest of the domain model, it can become cumbersome orchestrating between them
2. Domain service functions, while useful for orchestrating behavior, are often not sufficient in maintaining the state you need across these groups of entities (consistency boundaries)
3. Think of aggregates as public classes / entry points, and all other entities and value objects are private
   3a. Aggregates will abstract away which batches we send to the allocate domain function, but rather the allocate service function just specifies which Product it wants the allocation performed on (by SKU)
   3b. This is what we mean by consistency boundary: it abstracts away which entities, and which rows in db it will work on, and allow you to maintain state around it to keep your business rules in check

Solution

1. We will use a Product aggregate as the entry point to allocations in our system. this will be a class that maintains any state it needs to keep the variants its in charge of true
   1a. We will implement versioning on the Product aggregate to throw error on any concurrent tx of same product, effectively locking all related batches, regardless if they are being updated. NOTE: not all aggregates need this -- depends on invariants
   1b. We will change Tx isolation level to **Repeatable Read** will throw any error if you try to update a row that is already being updated in a concurrent tx
2. This means we should only have **Repositories for Aggregates** as they are entry points to our domain model and maintain our business constraints, whatever they may be

Takeaways

1. **Your db repositories should only point to aggregates. NEVER have services access entities that are not aggregates**
   1a. Imagine a scenario where you edit a batch and allocate at the same time. If you just edit the batch (through Batch entity), db will only throw a serialization error if a concurrent Tx edits that same row. This would be a problem if you do this edit, and concurrently an allocation was done. Why? because allocate is now not running on the most up to date state, so an orderline could be allocated to a batch that it shouldn't ideally have been allocated to (eg., what if you change eta attribute)
2. **You should almost always run your domain services on the most up to date system state**.
   2a. its up to your domain model if you want to lock all underlying entities connected to an aggregate, but you 99.99% of the time want to do so. we implemented such with versioning, but you could also change db isolation level to serialization
   2b. Serialization isolation level has a huge performance cost, we found setting tx isolation level to Repeatable Read, and implementing an auto update every time our aggregate was used achieved the same thing in a more scalable way
