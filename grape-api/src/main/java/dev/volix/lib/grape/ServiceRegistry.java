package dev.volix.lib.grape;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

/**
 * A registry to register and get services based on their [Class].
 *
 * @author Tobias Büser
 * @since 0.1.0
 * @see Service
 */
public abstract class ServiceRegistry {

    private final Map<Class<? extends Service>, Service> registry = new HashMap<>();
    private final Map<Class<? extends Service>, List<Consumer<Service>>> callbacks = new HashMap<>();

    /**
     * Puts the [service] with given [key] into the registry.
     *
     * Any callback listening for a registration with this key will also get executed.
     *
     * @throws IllegalStateException If already a service with given class is registered
     */
    public <T extends Service> void register(Class<T> key, T service) {
        if(this.hasService(key)) {
            throw new IllegalStateException("There is already a service registered with class " + key.getSimpleName());
        }
        this.registry.put(key, service);

        List<Consumer<Service>> callbacks = this.callbacks.remove(key);
        if(callbacks != null) {
            callbacks.forEach(c -> c.accept(service));
        }
    }

    /**
     * Returns whether a provider with given [key] is registered
     */
    public <T extends Service> boolean hasService(Class<T> key) {
        return this.registry.containsKey(key);
    }

    /**
     * Returns an [Optional] of a provider, which has been registered with given [key].
     * Will return [Optional.EMPTY], if no provider has been found.
     */
    public <T extends Service> Optional<T> find(Class<T> key) {
        return (Optional<T>) Optional.ofNullable(this.registry.get(key));
    }

    /**
     * Tries to find a service with given [key].
     *
     * Calls the [callback] if a service has been found. If no service with given
     * key is registered currently, the consumer will be stored and executed when a
     * service with the key has been registered.
     */
    public <T extends Service> void get(Class<T> key, Consumer<T> callback) {
        Optional<T> provider = this.find(key);

        if(provider.isPresent()) {
            callback.accept(provider.get());
            return;
        }

        List<Consumer<Service>> callbacks = this.callbacks.getOrDefault(key, new ArrayList<>());
        callbacks.add((Consumer<Service>) callback);
        this.callbacks.put(key, callbacks);
    }

    /**
     * Tries to find a service with given [key].
     *
     * Completes the returned [CompletableFuture] if a service has been found.
     */
    public <T extends Service> CompletableFuture<T> get(Class<T> key) {
        CompletableFuture<T> future = new CompletableFuture<>();
        this.get(key, future::complete);
        return future;
    }

}
