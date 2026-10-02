-- Staging Reviews: review scores, feedback comments, and creation timestamps
SELECT
    review_id,
    order_id,
    CAST(review_score AS INTEGER) AS review_score,
    TRIM(review_comment_title) AS review_title,
    TRIM(review_comment_message) AS review_comment,
    CAST(review_creation_date AS TIMESTAMP) AS review_created_at,
    CAST(review_answer_timestamp AS TIMESTAMP) AS review_answered_at
FROM raw_olist_order_reviews;
