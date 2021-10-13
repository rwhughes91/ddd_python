# Ch 1 Domain Modeling

Notes

1. Not everything needs to be a method! You can define domain services as functions as well
2. These models define all of your business logic and rules

Takeaways

1. **These models should have ZERO dependencies**

# Ch 2 Repository Pattern

Notes

1. we didn't add a save method to our repository but that is very common
2. Common to have 1 repository that holds list/get/add for all aggregates + save for each type. Its just as common to have 1 repository for each aggregate for each type. Also common to have abstract repositories / interfaces for each aggregate. This allows you to add more custom methods / fields that you want on each implementation (more flexible). We will switch to this in chapter 5.

Takeaways

1. Different ORM packages around querying a database implement different APIs. In order to not depend on a specific ORM, we create an interface (a repository) around common db operations. We can then make our service layer depend on this interface and pass any defined repository you want
2. This points to a main concept of DDD. you create interfaces/repositories of infrastructure services your app layer will need and pass it in as a dependency so your app is very easily extensible and decoupled from infrastructure concerns

# Ch 3 Service Layer

Takeaways

1. These are your app services. They invoke your domain services and define an interface/entry points to your domain model.
2. Its important that these services depend on interfaces, rather than implementations. This promotes strong TDD and allows you to easily change infrastructure dependencies without having to rewrite any service

# TDD via Domain Model vs. Service Layer

Notes

1. When building a domain model, testing the model is very useful (in making sure it works). as your system matures, you tend to make less domain changes and a lot of infrastructure/scaling/refactoring changes.
2. Testing the service layer provides more business value, because it only works if domain model is working + infra concerns around it. as your system matures testing close to the end (integration tests) provide more value for every test written

Takeaways

1. Just freaking write tests, but testing too low breaks a lot of tests for every refactoring phase. Testing too far misses important details that are often overlooked / harder to write great test flows. We found focusing a lot on service layer to be the best, as it abstracts domain implementations but is close enough to still easily test all invariants/rules

# Ch 4 Unit of Work

Notes

1. There is significant overlap for each service in the service layer. Just about each function queries the database, runs some domain service, and commits the changes. We created an abstraction that automates this orchestration, called the unit of work pattern
2. One of the nice things about this pattern is that it abstracts away the aggregates/other db infra dependencies that would need to be passed to a service in the service layer. For instance, function A no longer needs ExampleRepositoryA, ExampleRepositoryB, and a db session corresponding to the type of repositories passed in (eg., SqlAlchemy). Rather, function A just needs the unit of work you created for a particular type of Repository (eg., SqlAlchemy UOW)
3. In this chapter we also stopped creating value objects and passing those in to the service layer, and just started passing in inputs we needed to create value object inside the service layer itself. The first way isn't a no no, but this change feels cleaner because now our transport layer is just validating payload input and calling app service.

Takeaways

1. Creating an N number of Repositories (for each aggregate) for each type M is pretty annoying (M x N), especially since your service layer will need to depend on N interfaces (of the same interface! which feels weird). To combat this, lots of teams create one repository for all entities for each type (M). This is fine and totally up to your team; however, UOW pattern abstracts away the (N) amount of repositories, so up to you!
2. We put our UOW inside the service layer folder, but you could very much argue that this is an adapter. it abstracts and works with a specific ORM implementation / repository implementation. However, functionally, UOW was made to make the service layer DRY.

# Ch 5 Aggregates and Consistency Boundaries

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

Notes

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
   2c. if the domain service is in no way connected to an invariant then you DO NOT need increment aggregate version number. In other words, the locking is really to guarantee a consistency boundary, if you are just updating an attribute, and there are no constraints or invariants around it, then you don't need to lock the underlying rows. This would improve the efficiency of our system.
   2d. With all of this said, if you don't know (and its often hard to tell), increment the version to be safe -- e.g., all of our Product methods increment version numbers

# Ch 6 Event-Driven Architecture

Problem

1. When things don't work out, like an allocation can't happen, we throw an error. Often, you want to do some side effect when these errors occur (like send an email notifying someone that Product is out of stock). We know we don't want our domain model dependent on infrastructure concerns, so a natural place seems to be in the service layer. BUT, there is a dissatisfaction with putting the logic of sending an email in the service layer because this violates SRE (Single Responsibility Principle)
2. Like we have done, we could depend on a repository / interface in the service layer and pass in the specific implementation when called (we could even have a lot of the email sending logic encapsulated inside this repository), but we will explore the benefits of **raising domain events**.
3. Rasing domain events allows you to generate a list of events that have happened and its up to the application calling it to respond in any way it wants. We don't' really want to pass in too much email sending logic (like templates, etc) into the repository we are using because the repo is an infrastructure concern, and the logic of this side effect belongs in the app layer.
   3a. Having a message bus and raising events via the domain model solves this problem. It also allows different instances of app layers (if you need that) to respond in different ways -- not super common to need more than 1 service layer
   3b. This solution satisfies SRE -- think about the fact that event handlers can raise events themselves (if an error occurs or something), and this solution creates a robust cascade of reaction without bloating our service layer

Solution

1. we will implement a message bus, and attach it to our UOW. it'll take a list of all events that happened, iterate through them and call the appropriate event handler. Events will be dataclasses with the attributes each handler needs.

Takeaway

1. You can still raise exceptions when input to the domain model is invalid or something, but you don't want to both raise an exception and raise a domain event. A general rule is that you raise exceptions if domain model is being used wrong, but you raise events when things happen during the invocation of a domain service
2. This solution, albeit not something you see a lot, is very appealing. As our repo's grow and move to production its common to need to add a lot of edge case logic to specific endpoints or functions. Using an internal message bus allows you to define these edge cases in its own file, without bloating actual application logic
3. Our current implementation of MessageBus, where it holds all side effect logic, also doesn't feel quite right. Its in the app layer, but it feels weird because app logic should be in the services file. In the next chapter we will fix this.

# Ch 7 Making our App an Event Bus

Problem

1. We saw the benefits and scalability of raising domain events, and because of how strong it is, we are going to take it a step further. What if, instead of some infra-based side effect, what if on an event we needed to run some domain service again. For instance, on editing a batch a qty, we may need to deallocate order lines and re apply allocate for that order line (if batch qty is now less than order line qty)

Solution

1. This means we are going to turn EVERYTHING to event handlers! Every app service starts by setting up a queue, instantiated with a particular event, and as these domain services run, they will add events to this queue!
   1a. This also re-highlights the benefits of this event-driven architecture, whenever we need to re-apply business logic to a state change in our system, we can raise an event, rather than bloating an app service with another domain service invocation!
2. This solution also removes all of the side effect logic from the MessageBus, like sending an email, and puts it with all of the other app service logic. We will rename this file from services to handlers.py.

Notes

1. This implementation is interesting, but there are improvements that can be made. First, returning an array of results and popping the 0 index is a solution that can be greatly improved upon. Secondly, all of our events are past-tense, despite them having not yet happened.
2. It also doesn't feel quite right that our events, which kick off our domain services, are in the models/events file. Our app layer is what is orchestrating which event goes to which handler, so beginning events don't necessarily feel like they belong here but are made up for the app to flow. TLDR, these aren't really domain events, but its not the end of the world if they are in here.
3. A current limitation of our solution is that it ONLY pulls events from seen aggregates. BUT, what if an infra side effect, like sending an email (which occurs outside the scope of domain services) needs to raise an event? Maybe retry something or respond to some particular failure

# Ch 8 Command and Command Handlers

Problem

1. See last section of ch 7

Solution

1. We are going to divide a line between command - things that kick off domain services and events - things that happened when things are running (domain or side effects). We will have our message bus treat these differently as well. Data returned or errors raised from commands will be captured and returned back to whatever invoked it.
2. Some differences: Commands will be imperative, fail noisily, and sent to recipient. Events will be past tense, fail independently, and will be broadcasted to all listeners

Notes

1. You may wonder if we should add retry logic to commands. The answer is: for part of the command you can. You don't want to retry commands that have bad inputs or commands where there are obvious errors that could raise on our side, but you can add retry logic around DB requests, etc.
2. This solution still does not allow side effect handlers, outside the scope of an aggregate, from adding events to the queue. Retry logic takes away the case of a failing side effect needing to add its own event to the queue, but we are still missing the case when a side effect needs to raise another event.

# Ch 8b Allowing Handlers to add Events to Queue

Notes

1. Now we could implement this in a few ways, but a couple that pop out are A: event handlers return events that needed to be added to queues, or handler raise events that need to be added to the queue.
   1a. The latter could be difficult since we added retry logic (so if we went this way we would need to remove retry and add failed handler back to queue for retires). The first one is interesting....our commands return responses and our entry points to our domain model, so they will ALWAYS raise events in the context of an aggregate.
   1b. Back to the later...if you go the raising route make sure to not create infinite loops of side effects (if a service is down or something)
2. We could add a queue on the UOW, and we can grab the raised events attached to that UOW and add them to the messagebus queue
3. We could also pass the messagebus instance to the handlers and extend the queue in the handler ourselves (or pass a fn that adds to the queue)
   3a. typing is an issue here because of circular dependencies

Solution

1. We went with #3, it felt the cleanest

# Ch 9 Event-Driven Architecture with Other Services

Notes

1. One of the coolest parts of this event bus we have is that it can be triggered via CLI, HTTP, from a message broker, or whatever **without any additional mapping**
2. This architecture also makes it very natural to raise events by our service, so other services can react to it!
3. This chapter will be about publishing external events, and setting up a new transport as a message broker consumer

Problem

1. We are lacking a central file to keep track of external events we consume and publish to. For large services with hundreds of events this can really help.
2. We have no retry logic in our app services/handlers when concurrent transactions fail from serialization errors

Takeaway

1. When designing microservices, and deciding how to split up your system, make sure to not split you system up by nouns, but to **split up your system by verbs**
2. Communication between these services should be done with some message broker/event bus.
3. **Event sourcing** is a collection/store of events that have happened, and its common to keep these so you can have a list of state changes and services that have failed can know where they failed (via sequential IDs) and apply these events to have eventual consistency.
4. Microservices should only model things they care about. A Product model from service A may look different than service B and thats ideal. Microservices are also consistency boundaries just like Aggregates: they are responsible for making sure their variants are true at the time of committing

Current State of Project

1. So at this point we have a solid set up. We have an extremely testable architecture and our application depends on interfaces, not implementations (DIP). Additionally, we set up a UOW + Aggregates to have atomic operations with consistency boundaries. Lastly, we set up an event bus, to modularize everything into its own handler (SRP), which helps with refactoring and testing.
2. The next 2 chapters are interesting and tbh not often seen. Next chapter will separate out our views (list batches) from our commands (allocate/write operations) to help with efficiency and the last chapter will incorporate dependency injection

# Ch 10 Command-Query Responsibility Segregation (CQRS)

Overview

1. CQRS, often done across services (but can be done within a single service too), is an interesting idea but can add unnecessary complexity to a system. Typically when your system is using CRUD, and you don't need complex domain logic, this isn't necessary.
   1a. Honestly, in super simple systems writing domain models is unnecessary too (though the benefits of passing dependencies down from transport to app + internal event bus are still great for the simplest systems).
2. CQRS is the basic idea that reads (queries) and writes (commands) are different, so they should be treated differently (or have their responsibilities segregated, if you will)

Notes

1. Domain models are for commands/writes
   1a. We’ve spent a lot of talking about how to build software that enforces the rules of our domain. These rules, or constraints, will be different for every application, and they make up the interesting core of our systems.
   1b. To apply these rules properly, we needed to ensure that operations were consistent, and so we introduced patterns like Unit of Work and Aggregate that help us commit small chunks of work.
   1c. To communicate changes between those small chunks, we introduced the Domain Events pattern so we can write rules like "When stock is damaged or lost, adjust the available quantity on the batch, and reallocate orders if necessary."
2. All of this complexity exists so we can enforce rules when we change the state of our system. We’ve built a flexible set of tools for writing data. What about queries?
   1a. Most people will not purchase our products :(; however, we will get a LOT of views to see our products. How can we make this more efficient? CQRS argues that you can cache views, sacrifice consistency for performance. Because our write operations will run off the current state of your system, its okay to show views that are slightly out of date.
   2b. Example: let’s imagine that Bob and Harry both visit the page at the same time. Harry goes off to make coffee, and by the time he returns, Bob has already bought the last dresser. When Harry places his order, we send it to the allocation service, and because there’s not enough stock, we have to refund his payment or buy more stock and delay his delivery.
   3c. This insight is key to understanding why reads can be safely inconsistent: we’ll always need to check the current state of our system when we come to allocate, because all distributed systems are inconsistent. **As soon as you have a web server and two customers, you have the potential for stale data.**
3. Its always felt weird that we put list_batches and list_products as commands and in our handlers. Even if you decide not to go with CQRS, its a good idea to move views into their own spot of the system
4. Implementing views is a bit different than one first expects
   4a. Its not very efficient to use our repositories. For one, our repositories point to aggregates and we may want to view grab random data by certain conditions, sorted in specific ways, with different types of joins. If we used our repository, it would be much slower than it needs to be. In fact, writing raw sql to sqlalchemy would be the most efficient way to do this. We could have sqlalchemy models that get you lists and that could solve this problem too.
   4b. Secondly, our reads do not need our domain models, so we dont want our ORM to map the results to these objects. Again, raw sql prevents this. Using sqlalchemy models would NOT solve this. We would need to map to sqlalchemy models and then to output DTO.
   4c. ORMs can also lead to n+1 problems (not often), but raw sql again solves this issue. To be fair, sqlalchemy is great at preventing this, and uses DB views in an amazing way.
   4d. As weird as it sounds, using raw sql for views is actually the best way to handle this.
5. Another common feature in CQRS (even when done in the same service) is to have a **denormalized data source**, which makes reading even faster (no joins -- like WAY faster -- faster than even the most perfect indexes provide), and greatly simplifies our sql queries
6. Lastly, we need a way to update this read table, so we raise Events and make event handlers to update the Db! Important Note: we have repeatable read as an isolation level for our DB. We aren't implementing aggregates so serialization errors will happen a lot less, but will still happen. If we had another database, that had the default isolation level **Read Committed**, these serialization errors wouldn't happen at all (which gives a nudge to making view their own service).

# Ch 11 Dependency Injection

Problem

1. So currently, for every single adapter we have, we pass it into our uow to pass to our messagebus. Its not a big deal, but for every single endpoint we need to create a new instance (we need to do this because our classes mutate their data and will be shared across threads -- so its safer to init in each endpoint). All of this, especially when our app gets very large, is cumbersome because of the repetition.
2. So we want to create a class that orchestrates our adapters, and gives us a new message bus every time its called

Notes

1. We will be using DI to orchestrate our adapters, but we can also use this bootstrap class to inject event handlers and/or command handlers into the messagebus. Maybe you only want your flask app to send emails on OutOfStock or something.
2. Earlier we decided to add adapters to our UOW, but remember you could also pass these to the message bus

Solution

1. We will use dependency injection, or a bootstrap class to help us orchestrate. More often than not, a lot of our adapters will be used together (like Fake\*Adapters), so DI can help a lot with this.

# Outstanding Problems

1. retry logic for serialization errors that happen from concurrent transactions
2. it would be very easy to forget to increment the version number of our Product aggregate
