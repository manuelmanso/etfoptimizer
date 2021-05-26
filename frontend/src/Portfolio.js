import React from "react";
import PropTypes from "prop-types";
import CircularProgress from "@material-ui/core/CircularProgress";
import Typography from "@material-ui/core/Typography";
import Button from "@material-ui/core/Button";
import DownloadIcon from "@material-ui/icons/GetApp";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";

import { Alert, AlertTitle } from "@material-ui/lab";

class Portfolio extends React.Component {
    static propTypes = {
        portfolio: PropTypes.object,
        loading: PropTypes.bool.isRequired,
        error: PropTypes.string,
        onCloseError: PropTypes.func.isRequired,
        assetRounding: PropTypes.number.isRequired,
    };

    componentDidMount() {
        this.interval = setInterval(this.tick, 1000);
    }

    componentWillUnmount() {
        clearInterval(this.interval);
    }

    componentDidUpdate(prevProps) {
        if (!prevProps.loading && this.props.loading) {
            this.setState({ secondsElapsed: 0 });
        }
    }

    state = {
        secondsElapsed: 0,
    };

    render() {
        const { secondsElapsed } = this.state;
        const { portfolio, loading, error, onCloseError, assetRounding } = this.props;

        return (
            <React.Fragment>
                <Typography variant="subtitle1" component="h2" style={{ float: "right", margin: "15px" }}>
                    {"Time elapsed: " + secondsElapsed + "s"}
                </Typography>
                <Typography variant="h5" component="h2" style={{ margin: "15px", fontWeight: "bold" }}>
                    Optimized Portfolio
                </Typography>

                {error != null ? (
                    <Alert severity="error" style={{ marginLeft: "5px", marginRight: "5px", marginBottom: "20px" }} onClose={onCloseError}>
                        <AlertTitle>Error</AlertTitle>
                        {error}
                    </Alert>
                ) : loading ? (
                    <div style={{ display: "flex", justifyContent: "center", margin: "15px" }}>
                        <CircularProgress />
                    </div>
                ) : (
                    <React.Fragment>
                        <img
                            style={{ float: "right", maxWidth: "50%", margin: "10px" }}
                            src={`data:image/png;base64,${portfolio.efficientFrontierImage}`}
                            alt="Efficient Frontier Plot"
                        />
                        <Typography variant="body1" component="h2" style={{ margin: "15px", marginTop: "75px" }}>
                            {"Sharpe ratio: " + portfolio.sharpeRatio.toFixed(2)}
                        </Typography>
                        <Typography variant="body1" component="h2" style={{ margin: "15px" }}>
                            {"Expected return: " + (portfolio.expectedReturn * 100).toFixed(2) + "%"}
                        </Typography>
                        <Typography variant="body1" component="h2" style={{ margin: "15px" }}>
                            {"Annual Volatility: " + (portfolio.annualVolatility * 100).toFixed(2) + "%"}
                        </Typography>
                        <Typography variant="body1" component="h2" style={{ margin: "15px" }}>
                            {"ETFs matching filters: " + portfolio.ETFsMatchingFilters}
                        </Typography>
                        <Typography variant="body1" component="h2" style={{ margin: "15px" }}>
                            {"ETFs used for optimization: " + portfolio.ETFsUsedForOptimization}
                        </Typography>
                        <Typography variant="h6" component="h2" style={{ marginLeft: "5px", marginTop: "125px" }}>
                            {"Portfolio: (" + portfolio.portfolioSize + " assets)"}
                        </Typography>
                        <Typography variant="body1" component="h2" style={{ margin: "15px" }}>
                            {"Initial Value: " + portfolio.initialValue.toLocaleString() + "€"}
                        </Typography>
                        <Typography variant="body1" component="h2" style={{ margin: "15px" }}>
                            {"Leftover Funds: " + portfolio.leftoverFunds.toLocaleString() + "€"}
                        </Typography>
                        <Table size="small" aria-label="a dense table">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>ISIN</TableCell>
                                    <TableCell>Return</TableCell>
                                    <TableCell>Volatility</TableCell>
                                    <TableCell>Weight</TableCell>
                                    <TableCell>Shares</TableCell>
                                    <TableCell>Price</TableCell>
                                    <TableCell>Value (€)</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {portfolio.portfolio.map((etf) => (
                                    <TableRow key={etf.isin}>
                                        <TableCell component="th" scope="row">
                                            {etf.name}
                                        </TableCell>
                                        <TableCell component="th" scope="row">
                                            {etf.isin}
                                        </TableCell>
                                        <TableCell component="th" scope="row">
                                            {(etf.expectedReturn * 100).toFixed(2) + "%"}
                                        </TableCell>
                                        <TableCell component="th" scope="row">
                                            {(etf.volatility * 100).toFixed(2) + "%"}
                                        </TableCell>
                                        <TableCell component="th" scope="row">
                                            {(etf.weight * 100).toFixed(assetRounding >= 2 ? assetRounding - 2 : 0) + "%"}
                                        </TableCell>
                                        <TableCell component="th" scope="row">
                                            {etf.shares}
                                        </TableCell>
                                        <TableCell component="th" scope="row">
                                            {etf.price != null ? etf.price.toFixed(2) : ""}
                                        </TableCell>
                                        <TableCell component="th" scope="row">
                                            {etf.value.toLocaleString()}
                                        </TableCell>
                                    </TableRow>
                                ))}
                                <TableRow key={"123123sadas"}>
                                    <TableCell component="th" scope="row" style={{ fontWeight: "bold" }}>
                                        Portfolio
                                    </TableCell>
                                    <TableCell component="th" scope="row"></TableCell>
                                    <TableCell component="th" scope="row" style={{ fontWeight: "bold" }}>
                                        {(portfolio.totalWeight * 100).toFixed(2) + "%"}
                                    </TableCell>
                                    <TableCell component="th" scope="row"></TableCell>
                                    <TableCell component="th" scope="row"></TableCell>
                                    <TableCell component="th" scope="row" style={{ fontWeight: "bold" }}>
                                        {portfolio.totalValue.toLocaleString()}
                                    </TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>

                        <div style={{ display: "flex", justifyContent: "flex-end" }}>
                            <Button variant="contained" style={{ margin: "15px" }} endIcon={<DownloadIcon />} onClick={this.downloadPlot}>
                                Download Plot
                            </Button>
                            <Button
                                variant="contained"
                                style={{ margin: "15px" }}
                                endIcon={<DownloadIcon />}
                                onClick={this.downloadPortfolio}
                            >
                                Download Portfolio
                            </Button>
                        </div>
                    </React.Fragment>
                )}
            </React.Fragment>
        );
    }

    downloadPlot = () => {
        const { portfolio } = this.props;

        const a = document.createElement("a");
        a.href = `data:image/png;base64,${portfolio["efficientFrontierImage"]}`;
        a.download = "EfficientFrontier.png";
        a.click();
    };

    downloadPortfolio = () => {
        const { portfolio } = this.props;

        let portfolioToDownload = { ...portfolio };
        delete portfolioToDownload["efficientFrontierImage"];

        let json = JSON.stringify(portfolioToDownload, undefined, 4);

        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([json], { type: "text/json" }));
        a.download = "portfolio.json";
        a.click();
    };

    tick = () => {
        if (this.props.loading) {
            this.setState({ secondsElapsed: this.state.secondsElapsed + 1 });
        }
    };
}

export default Portfolio;
