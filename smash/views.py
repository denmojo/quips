import datetime
import json
import logging
import sqlite3
from collections import defaultdict
from sqlalchemy.sql.expression import func, select
from flask import render_template, Markup, request, redirect, abort, session, g

from smash.models_sqlalchemy import *
from smash import app, conf, db, limiter, xcaptcha

logger = logging.getLogger(__name__)

TIME_FORMAT="%H:%M:%S %m/%d/%Y"


def timestamp():
    return datetime.datetime.now().strftime(TIME_FORMAT)


def to_unixtime(ts):
    """ Converts from a time string to a unixtime """
    return datetime.datetime.strptime(ts, TIME_FORMAT).strftime("%s")


def message(level, msg):
    return render_template(
        "message.html",
        alertclass=level,
        message=msg,
        title="Message"
    )


@app.before_request
def before_request():
    g.appname = conf.config['APPNAME']
    g.appbrand = conf.config['APPBRAND']


@app.route('/')
def index():
    welcome = conf.config['MOTD']
    news = ("<p><b>{}</b></p><h4>{} running on quips database"
            " engine launched today</h4>").format(
                datetime.datetime.now().strftime("%m/%d/%Y"),
                conf.config['APPNAME']
            )

    return render_template(
        "index.html",
        title="Quips",
        welcometext=welcome,
        newstext=news
    )


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        if request.form["secret"] == conf.config['ADMINSECRET']:
            session['authorized'] = True
            return redirect("queue", code=303)

    return render_template(
        "login.html",
    )


@app.route('/latest')
def latest():
    quotes = Quote.query.filter_by(approved=True).order_by(Quote.id.desc()).all()
    allquotes = len(quotes)
    quotes = quotes[:10]

    if len(quotes)>0:
        # Replace line breaks with html breaks and escape special characters
        for quote in quotes:
            quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

        return render_template(
            "latest.html",
            title="Latest",
            quotes=quotes,
            numpages=1 + allquotes//10,
            curpage=0,
            page_type="latest"
        )
    else:
        return message("alert-warning", "No quips in the database.")


@app.route('/latest/<int:page>')
def latest_page(page):
    allquotes = len(Quote.query.filter_by(approved=True).order_by(Quote.id.desc()).all())
    quotes = Quote.query.filter_by(approved=True).order_by(Quote.id.desc()).all()[(page-1)*10:page*10]

    for quote in quotes:
        quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

    return render_template(
        "latest.html",
        title="Latest - page {}".format(page),
        quotes=quotes,
        numpages=1 + allquotes//10,
        curpage=page-1,
        page_type="latest"
    )


@app.route('/top')
def top():
    quotes = Quote.query.filter_by(approved=True).order_by(Quote.rating.desc()).all()
    allquotes = len(quotes)
    quotes = quotes[:10]

    if len(quotes)>0:
        # Replace line breaks with html breaks and escape special characters
        for quote in quotes:
            quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

        return render_template(
            "latest.html",
            title="Top",
            quotes=quotes,
            numpages=1 + allquotes//10,
            curpage=0,
            page_type="top"
        )
    else:
        return message("alert-warning", "No quips in the database.")


@app.route('/top/<int:page>')
def top_page(page):
    allquotes = len(Quote.query.filter_by(approved=True).order_by(Quote.rating.desc()).all())
    quotes = Quote.query.filter_by(approved=True).order_by(Quote.rating.desc()).all()[(page-1)*10:page*10]

    for quote in quotes:
        quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

    return render_template(
        "latest.html",
        title="Top - page {}".format(page),
        quotes=quotes,
        numpages=1 + allquotes//10,
        curpage=page-1,
        page_type="top"
    )

@app.route('/browse')
def browse():
    quotes = Quote.query.filter_by(approved=True).order_by(Quote.id.asc()).all()
    allquotes = len(quotes)
    quotes = quotes[:10]

    if len(quotes)>0:
        # Replace line breaks with html breaks and escape special characters
        for quote in quotes:
            quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

        return render_template(
            "latest.html",
            title="Latest",
            quotes=quotes,
            numpages=1 + allquotes//10,
            curpage=0,
            page_type="browse"
        )
    else:
        return message("alert-warning", "No quips in the database.")

@app.route('/browse/<int:page>')
def browse_page(page):
    allquotes = len(Quote.query.filter_by(approved=True).order_by(Quote.id.asc()).all())
    quotes = Quote.query.filter_by(approved=True).order_by(Quote.id.asc()).all()[(page-1)*10:page*10]

    for quote in quotes:
        quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

    return render_template(
        "latest.html",
        title="Latest - page {}".format(page),
        quotes=quotes,
        numpages=1 + allquotes//10,
        curpage=page-1,
        page_type="browse"
    )

@app.route('/random')
def random():
    quotes = Quote.query.filter_by(approved=True).order_by(func.random()).all()
    allquotes = len(quotes)
    quotes = quotes[:10]

    if len(quotes)>0:
        # Replace line breaks with html breaks and escape special characters
        for quote in quotes:
            quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

        return render_template(
            "latest.html",
            title="Random",
            quotes=quotes,
            numpages=1 + allquotes//10,
            curpage=0,
            page_type="random"
        )
    else:
        return message("alert-warning", "No quips in the database.")

@app.route('/random/<int:page>')
def random_page(page):
    allquotes = len(Quote.query.filter_by(approved=True).order_by(func.random()).all())
    quotes = Quote.query.filter_by(approved=True).order_by(func.random()).all()[(page-1)*10:page*10]

    for quote in quotes:
        quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

    return render_template(
        "latest.html",
        title="Latest - page {}".format(page),
        quotes=quotes,
        numpages=1 + allquotes//10,
        curpage=page-1,
        page_type="random"
    )


@app.route('/queue')
def queue():
    if not session.get('authorized'):
        return message("alert-danger", "You are not authorized to view this page.")

    quotes = Quote.query.filter_by(approved=False).order_by(Quote.id).all()

    if len(quotes)>0:
        # Replace line breaks with html breaks and escape special characters
        for quote in quotes:
            quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

        return render_template(
            "queue.html",
            title="Queue",
            quotes=quotes
        )
    else:
        return message("alert-warning", "No quotes in the database.")


@app.route('/moderate', methods=['POST'])
def moderate():
    if not session.get('authorized'):
        return message("alert-danger", "You are not authorized to perform this action.")

    if request.form['submit'] == "Approve":
        quote = Quote.query.filter_by(id=request.form['quoteid']).first()
        quote.approved = True
        db.session.commit()

        return message("alert-success", "Quip approved.")

    elif request.form['submit'] == "Delete":
        quote = Quote.query.filter_by(id=request.form['quoteid']).first()
        # Delete dangling tags (alive only with current Quote)
        dangling_tags = [tag for tag in quote.tags if tag.quotes.count() == 1]
        for tag in dangling_tags:
            db.session.delete(tag)
        db.session.delete(quote)
        db.session.commit()

        return message("alert-success", "Quip deleted.")

    abort(501)


@app.route('/quip/<int:id>')
def quote(id):
    quote = Quote.query.filter_by(id=id, approved=True).first()

    if quote is None:
        return render_template(
            "message.html",
            alertclass="alert-warning",
            message="No such quip."
        )
    else:
        quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')
        return render_template(
            "latest.html",
            title="Quip #{}".format(quote.id),
            quotes=[quote,],
            numpages=1,
            curpage=0,
            page_type="quote"
        )


@app.route('/tag/<tagname>')
def tag(tagname):
    tag = Tag.query.filter_by(name=tagname).first()

    if tag is not None:
        if len(list(tag.quotes))>0:
            allquotes = len(list(tag.quotes))
            tag.quotes = tag.quotes[:10]

            # Replace line breaks with html breaks and escape special characters
            for quote in tag.quotes:
                quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

            return render_template(
                "latest.html",
                title="Tag - {}".format(tagname),
                quotes=tag.quotes,
                numpages=1 + allquotes//10,
                curpage=0,
                page_type="tag/{}".format(tagname)
            )
    else:
        return message("alert-warning", "No quotes with this tag.")


@app.route('/tag/<tagname>/<int:page>')
def tag_page(tagname, page):
    tag = Tag.query.filter_by(name=tagname).first()

    if len(list(tag.quotes))>0:
        allquotes = len(list(tag.quotes))
        tag.quotes = tag.quotes[(page-1)*10:page*10]

        for quote in tag.quotes:
            quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

        return render_template(
            "latest.html",
            title="Tag - {} - page {}".format(tagname, page),
            quotes=tag.quotes,
            numpages=1 + allquotes//10,
            curpage=0,
            page_type="tag/{}".format(tagname)
        )


@app.route('/tags')
def tags():
    tags = Tag.query.order_by(Tag.name).distinct().all()
    tags = list(set([x.name for x in tags]))

    return render_template(
        "tags.html",
        title="Tags",
        tags=tags
    )


@app.route('/search/<query>')
def search(query):
    quotes = Quote.query.filter_by(approved=True).filter(Quote.content.ilike('%{}%'.format(query))).order_by(Quote.id.desc()).all()

    allquotes = len(quotes)
    quotes = quotes[:10]

    if len(quotes)>0:
        # Replace line breaks with html breaks and escape special characters
        for quote in quotes:
            quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

        return render_template(
            "search.html",
            title="Search for: {}".format(query),
            quotes=quotes,
            numpages=1 + allquotes//10,
            curpage=0,
            page_type="search",
            search_query=query
        )
    else:
        return message("alert-warning", "No quotes in the database.")


@app.route('/search/<query>/<int:page>')
def search_page(query, page):
    allquotes = len(Quote.query.filter_by(approved=True).\
                                filter(Quote.content.ilike('%{}%'.format(query))).\
                                order_by(Quote.id.desc()).all())
    quotes = Quote.query.filter_by(approved=True).\
                         filter(Quote.content.ilike('%{}%'.format(query))).\
                         order_by(Quote.id.desc()).all()[(page-1)*10:page*10]

    for quote in quotes:
        quote.content = str(Markup.escape(quote.content)).replace('\n', '</br>')

    return render_template(
        "search.html",
        title="Search for: {} - page {}".format(query, page),
        quotes=quotes,
        numpages=1 + allquotes//10,
        curpage=page-1,
        page_type="search",
        search_query=query
    )

@app.route('/slack', methods=['POST'])
@limiter.limit("5 per minute;25 per day")
def slack():
    quote_body = request.form["text"]
    quote = Quote(quote_body, request.remote_addr, timestamp())
    db.session.add(quote)
    db.session.commit()

    return json.dumps({'status' : 'success'})


@app.route('/add', methods=['GET', 'POST'])
@limiter.limit("5 per minute;25 per day")
def add_new():
    if request.method == 'POST':
        if xcaptcha.verify():
            if request.form['submit'] == "Submit":
                quote_body = request.form["newquote"]
                quote_tags = request.form["tags"].split(',')

                quote = Quote(quote_body, request.remote_addr, timestamp())
                quote_tags = [Tag(tag) for tag in quote_tags]

                for tag in quote_tags:
                    dbtag = Tag.query.filter_by(name=tag.name).first()
                    if dbtag is not None:
                        quote.tags.append(dbtag)
                    else:
                        quote.tags.append(tag)
                #quote.tags.extend(quote_tags)

                db.session.add(quote)
                db.session.commit()

                return render_template(
                    "message.html",
                    alertclass="alert-success",
                    message="Quote added succesfully. It will need to be reviewed by the administrators before it shows up."
                )

            elif request.form['submit'] == "Preview":
                preview = Quote(request.form['newquote'], request.remote_addr, timestamp())
                preview_tags = request.form["tags"].split(',')
                preview.approved = True
                preview.tags = [Tag(tag) for tag in preview_tags]
            
                return render_template(
                    "latest.html",
                    title="Quip preview",
                    quotes=[preview,],
                    numpages=1,
                    curpage=0,
                    page_type="quote"
                )
            else:
                abort(501)
        else:
            return render_template(
                "add.html",
                alertclass="alert-danger",
                message="hCaptcha verification failed, please complete the hCaptcha.",
                title="Add new - Complete hCaptcha"
            )

    elif request.method == 'GET':
        return render_template(
            "add.html",
            title="Add new"
        )

@app.route('/upvote', methods=['POST'])
@limiter.limit("5 per minute")
def upvote_post():
    if request.method == "POST":

        data_received = json.loads(request.data) 
        
        quip = Quote.query.filter_by(id=data_received['postid']).first()
        
        if quip:
            setattr(quip, "rating", quip.rating + 1)
            db.session.commit()
                 
            return json.dumps({'status' : 'success'})
        return json.dumps({'status' : 'no post found'})
    return redirect(url_for('index'))

@app.route('/downvote', methods=['POST'])
@limiter.limit("1 per minute")
def downvote_post():
    if request.method == "POST":

        data_received = json.loads(request.data) 
        
        quip = Quote.query.filter_by(id=data_received['postid']).first()
        
        if quip:
            setattr(quip, "rating", quip.rating - 1)
            db.session.commit()
                 
            return json.dumps({'status' : 'success'})
        return json.dumps({'status' : 'no post found'})
    return redirect(url_for('index'))

@app.route('/export', methods=['GET'])
@limiter.limit("5 per minute")
def export_get():
    """exfiltrates all approved quotes from the database from an unauthenticated endpoint."""
    all_tag_names = Tag.query.all()
    tag_names = {}
    for tag in all_tag_names:
        tag_names[tag.id] = tag.name

    all_tags = db.session.query(tags_to_quotes).all()
    tag_map = defaultdict(list)
    for tag in all_tags:
        tag_map[tag.quoteid].append(tag_names[tag.tagid])

    result = []
    all_quotes = Quote.query.filter_by(approved=True).order_by(Quote.id.desc()).all()

    for q in all_quotes:
        result.append({
            'content': q.content,
            'rating': q.rating,
            'authorIP': q.author_ip,
            'time': q.time,
            'tags': tag_map[q.id],
        })
    return json.dumps(result), 200, {'Content-Type': 'application/json'}
    
