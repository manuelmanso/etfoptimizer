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
                <Typography variant="h6" component="h2" style={{ margin: "15px", fontWeight: "bold" }}>
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
                        <Typography variant="body2" component="h2" style={{ margin: "5px" }}>
                            {"Sharpe ratio: " + portfolio.sharpeRatio.toFixed(2)}
                        </Typography>
                        <Typography variant="body2" component="h2" style={{ margin: "5px" }}>
                            {"Expected return: " + (portfolio.expectedReturn * 100).toFixed(2) + "%"}
                        </Typography>
                        <Typography variant="body2" component="h2" style={{ margin: "5px" }}>
                            {"Annual Volatility: " + (portfolio.annualVolatility * 100).toFixed(2) + "%"}
                        </Typography>
                        <Typography variant="h6" component="h2" style={{ marginLeft: "5px", marginTop: "25px" }}>
                            {"Portfolio: (" + portfolio.portfolioSize + " assets)"}
                        </Typography>
                        <Table size="small" dense aria-label="a dense table">
                            <TableHead>
                                <TableRow>
                                    <TableCell>ETF</TableCell>
                                    <TableCell align="left">Weight</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {portfolio.portfolio.map((etf) => (
                                    <TableRow key={etf.name}>
                                        <TableCell component="th" scope="row">
                                            {etf.ETF}
                                        </TableCell>
                                        <TableCell align="left">
                                            {(etf.weight * 100).toFixed(assetRounding >= 2 ? assetRounding - 2 : 0) + "%"}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                        <div style={{ display: "flex", justifyContent: "flex-end" }}>
                            <Button
                                variant="contained"
                                style={{ margin: "15px" }}
                                endIcon={<DownloadIcon />}
                                onClick={this.downloadPortfolio}
                            >
                                Download
                            </Button>
                        </div>
                    </React.Fragment>
                )}
            </React.Fragment>
        );
    }

    downloadPortfolio = () => {};

    tick = () => {
        if (this.props.loading) {
            this.setState({ secondsElapsed: this.state.secondsElapsed + 1 });
        }
    };
}

export default Portfolio;
