package com.example.shop.domain.order.support;

public interface CustomerCreditSupport {

    void ensureCustomerCanCreateOrder(Long customerId);
}
